"""
Message Bus implementation for inter-agent communication.
Provides thread-safe publish-subscribe messaging with priority queuing.
"""

import threading
import queue
import time
from typing import Dict, List, Callable, Optional, Set
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from .message_types import Message, Priority, MessageType

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Central message bus for agent communication.
    Implements publish-subscribe pattern with topic-based routing.
    """

    def __init__(self, max_queue_size: int = 10000):
        """
        Initialize the message bus.

        Args:
            max_queue_size: Maximum number of messages in queue before backpressure
        """
        self.max_queue_size = max_queue_size

        # Topic subscriptions: topic -> list of (agent_id, callback)
        self._subscriptions: Dict[str, List[tuple[str, Callable]]] = defaultdict(list)

        # Priority queues for message processing
        self._high_priority_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._medium_priority_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._low_priority_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)

        # Dead letter queue for failed messages
        self._dead_letter_queue: queue.Queue = queue.Queue()

        # Thread-safe locks
        self._subscription_lock = threading.RLock()
        self._running = False
        self._dispatcher_thread: Optional[threading.Thread] = None

        # Metrics
        self._metrics = {
            "messages_published": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "messages_dropped": 0,
            "total_latency_ms": 0.0,
        }
        self._metrics_lock = threading.Lock()

        # Request-response tracking
        self._pending_requests: Dict[str, threading.Event] = {}
        self._responses: Dict[str, Message] = {}
        self._request_lock = threading.Lock()

    def start(self):
        """Start the message bus dispatcher"""
        if self._running:
            logger.warning("Message bus already running")
            return

        self._running = True
        self._dispatcher_thread = threading.Thread(
            target=self._dispatch_messages, name="MessageBusDispatcher", daemon=True
        )
        self._dispatcher_thread.start()
        logger.info("Message bus started")

    def stop(self):
        """Stop the message bus dispatcher"""
        if not self._running:
            return

        self._running = False
        if self._dispatcher_thread:
            self._dispatcher_thread.join(timeout=5.0)

        logger.info("Message bus stopped")

    def subscribe(self, topic: str, agent_id: str, callback: Callable[[Message], None]):
        """
        Subscribe to a topic.

        Args:
            topic: Topic pattern (supports wildcards: audio.*, *.error)
            agent_id: Unique identifier for the subscribing agent
            callback: Function to call when message received
        """
        with self._subscription_lock:
            self._subscriptions[topic].append((agent_id, callback))
            logger.debug(f"Agent {agent_id} subscribed to {topic}")

    def unsubscribe(self, topic: str, agent_id: str):
        """
        Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from
            agent_id: Agent identifier
        """
        with self._subscription_lock:
            if topic in self._subscriptions:
                self._subscriptions[topic] = [
                    (aid, cb)
                    for aid, cb in self._subscriptions[topic]
                    if aid != agent_id
                ]
                logger.debug(f"Agent {agent_id} unsubscribed from {topic}")

    def publish(self, message: Message) -> bool:
        """
        Publish a message to the bus.

        Args:
            message: Message to publish

        Returns:
            True if message was queued, False if dropped due to backpressure
        """
        # Select appropriate queue based on priority
        target_queue = self._get_queue_for_priority(message.priority)

        try:
            # Try to put message in queue (non-blocking)
            target_queue.put_nowait(message)

            with self._metrics_lock:
                self._metrics["messages_published"] += 1

            logger.debug(
                f"Published message {message.message_id} to topic {message.topic}"
            )
            return True

        except queue.Full:
            # Queue is full - handle backpressure
            if message.priority == Priority.LOW:
                # Drop low priority messages
                with self._metrics_lock:
                    self._metrics["messages_dropped"] += 1
                logger.warning(f"Dropped low priority message {message.message_id}")
                return False
            else:
                # Block for high/medium priority (with timeout)
                try:
                    target_queue.put(message, timeout=1.0)
                    with self._metrics_lock:
                        self._metrics["messages_published"] += 1
                    return True
                except queue.Full:
                    with self._metrics_lock:
                        self._metrics["messages_dropped"] += 1
                    logger.error(
                        f"Failed to queue message {message.message_id} - queue full"
                    )
                    return False

    def request(self, message: Message, timeout: float = 5.0) -> Optional[Message]:
        """
        Send a request and wait for response.

        Args:
            message: Request message
            timeout: Maximum time to wait for response (seconds)

        Returns:
            Response message or None if timeout
        """
        if not message.correlation_id:
            message.correlation_id = message.message_id

        message.message_type = MessageType.REQUEST

        # Create event for response tracking
        response_event = threading.Event()
        with self._request_lock:
            self._pending_requests[message.correlation_id] = response_event

        # Publish request
        if not self.publish(message):
            with self._request_lock:
                del self._pending_requests[message.correlation_id]
            return None

        # Wait for response
        if response_event.wait(timeout):
            with self._request_lock:
                response = self._responses.pop(message.correlation_id, None)
                del self._pending_requests[message.correlation_id]
            return response
        else:
            # Timeout
            with self._request_lock:
                if message.correlation_id in self._pending_requests:
                    del self._pending_requests[message.correlation_id]
            logger.warning(f"Request {message.correlation_id} timed out")
            return None

    def respond(self, original_message: Message, response_payload: Dict) -> bool:
        """
        Send a response to a request.

        Args:
            original_message: The original request message
            response_payload: Response data

        Returns:
            True if response was sent
        """
        if not original_message.correlation_id:
            logger.error("Cannot respond to message without correlation_id")
            return False

        response = Message(
            topic=original_message.topic + ".response",
            sender="response_handler",
            payload=response_payload,
            correlation_id=original_message.correlation_id,
            message_type=MessageType.RESPONSE,
            priority=original_message.priority,
        )

        # Check if anyone is waiting for this response
        with self._request_lock:
            if original_message.correlation_id in self._pending_requests:
                self._responses[original_message.correlation_id] = response
                self._pending_requests[original_message.correlation_id].set()
                return True

        return False

    def get_metrics(self) -> Dict:
        """Get current metrics"""
        with self._metrics_lock:
            metrics = self._metrics.copy()

        # Calculate average latency
        if metrics["messages_delivered"] > 0:
            metrics["avg_latency_ms"] = (
                metrics["total_latency_ms"] / metrics["messages_delivered"]
            )
        else:
            metrics["avg_latency_ms"] = 0.0

        # Queue depths
        metrics["queue_depth_high"] = self._high_priority_queue.qsize()
        metrics["queue_depth_medium"] = self._medium_priority_queue.qsize()
        metrics["queue_depth_low"] = self._low_priority_queue.qsize()
        metrics["dead_letter_count"] = self._dead_letter_queue.qsize()

        return metrics

    def _get_queue_for_priority(self, priority: Priority) -> queue.Queue:
        """Get the appropriate queue for a message priority"""
        if priority == Priority.HIGH:
            return self._high_priority_queue
        elif priority == Priority.MEDIUM:
            return self._medium_priority_queue
        else:
            return self._low_priority_queue

    def _dispatch_messages(self):
        """Main dispatcher loop - runs in separate thread"""
        logger.info("Message dispatcher started")

        while self._running:
            message = None

            # Check queues in priority order
            try:
                message = self._high_priority_queue.get_nowait()
            except queue.Empty:
                try:
                    message = self._medium_priority_queue.get_nowait()
                except queue.Empty:
                    try:
                        message = self._low_priority_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue

            if message:
                self._deliver_message(message)

        logger.info("Message dispatcher stopped")

    def _deliver_message(self, message: Message):
        """
        Deliver a message to all subscribers.

        Args:
            message: Message to deliver
        """
        start_time = time.perf_counter()

        # Find matching subscribers
        subscribers = self._find_subscribers(message.topic)

        if not subscribers:
            logger.debug(f"No subscribers for topic {message.topic}")
            return

        # Deliver to each subscriber
        for agent_id, callback in subscribers:
            try:
                callback(message)
                with self._metrics_lock:
                    self._metrics["messages_delivered"] += 1
            except Exception as e:
                logger.error(
                    f"Error delivering message {message.message_id} "
                    f"to agent {agent_id}: {e}"
                )
                with self._metrics_lock:
                    self._metrics["messages_failed"] += 1

                # Add to dead letter queue
                try:
                    self._dead_letter_queue.put_nowait((message, agent_id, str(e)))
                except queue.Full:
                    logger.error("Dead letter queue is full")

        # Record latency
        latency_ms = (time.perf_counter() - start_time) * 1000
        with self._metrics_lock:
            self._metrics["total_latency_ms"] += latency_ms

        logger.debug(
            f"Delivered message {message.message_id} to "
            f"{len(subscribers)} subscribers in {latency_ms:.2f}ms"
        )

    def _find_subscribers(self, topic: str) -> List[tuple[str, Callable]]:
        """
        Find all subscribers matching a topic.

        Supports wildcard matching:
        - audio.* matches audio.input.received, audio.analysis.complete, etc.
        - *.error matches vst.error, daw.error, etc.

        Args:
            topic: Topic to match

        Returns:
            List of (agent_id, callback) tuples
        """
        subscribers = []

        with self._subscription_lock:
            for sub_topic, subs in self._subscriptions.items():
                if self._topic_matches(topic, sub_topic):
                    subscribers.extend(subs)

        return subscribers

    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """
        Check if a topic matches a subscription pattern.

        Args:
            topic: Actual topic
            pattern: Subscription pattern (may contain wildcards)

        Returns:
            True if topic matches pattern
        """
        # Exact match
        if topic == pattern:
            return True

        # Wildcard matching
        topic_parts = topic.split(".")
        pattern_parts = pattern.split(".")

        if len(topic_parts) != len(pattern_parts):
            return False

        for topic_part, pattern_part in zip(topic_parts, pattern_parts):
            if pattern_part == "*":
                continue
            if topic_part != pattern_part:
                return False

        return True


# Global message bus instance
_global_bus: Optional[MessageBus] = None
_global_bus_lock = threading.Lock()


def get_message_bus() -> MessageBus:
    """Get the global message bus instance (singleton)"""
    global _global_bus

    if _global_bus is None:
        with _global_bus_lock:
            if _global_bus is None:
                _global_bus = MessageBus()
                _global_bus.start()

    return _global_bus
