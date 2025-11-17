"""
Message Bus Adapter for API
Bridges FastAPI endpoints with MAAPS message bus
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import uuid

from src.core.message_bus import get_message_bus, Message, Priority

logger = logging.getLogger(__name__)


class MessageBusAdapter:
    """
    Adapter to communicate with MAAPS agents via message bus
    """

    def __init__(self):
        self.message_bus = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.subscribers: Dict[str, Callable] = {}
        self.running = False

    async def start(self):
        """Initialize and start the adapter"""
        logger.info("Starting message bus adapter...")
        self.message_bus = get_message_bus()
        self.running = True

        # Subscribe to response topics
        self.message_bus.subscribe("api.response.*", "api_adapter", self._handle_response)

        # Subscribe to events for WebSocket broadcasting
        self._subscribe_to_events()

        logger.info("Message bus adapter started")

    async def stop(self):
        """Stop the adapter"""
        logger.info("Stopping message bus adapter...")
        self.running = False

        # Cancel all pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()

        logger.info("Message bus adapter stopped")

    def _subscribe_to_events(self):
        """Subscribe to agent events for WebSocket broadcasting"""
        event_topics = [
            "effects.parameter.change",
            "effects.chain.created",
            "effects.preset.recalled",
            "effects.scene.changed",
            "loop.record.started",
            "loop.record.stopped",
            "loop.playback.toggle",
            "loop.manipulate.complete",
            "sync.clock.tempo",
            "sync.clock.position",
            "sync.transport.control",
            "automation.scene.triggered",
            "automation.cue.fired",
            "automation.record.started",
            "automation.record.stopped",
            "system.agent.heartbeat",
            "system.agent.error"
        ]

        for topic in event_topics:
            self.message_bus.subscribe(topic, "api_adapter", self._handle_event)

    def _handle_response(self, message: Message):
        """Handle response messages from agents"""
        request_id = message.payload.get("request_id")
        if request_id and request_id in self.pending_requests:
            future = self.pending_requests[request_id]
            if not future.done():
                future.set_result(message.payload.get("data"))
            del self.pending_requests[request_id]

    def _handle_event(self, message: Message):
        """Handle event messages for WebSocket broadcasting"""
        # Import here to avoid circular dependency
        from api.websocket import websocket_manager

        # Broadcast to WebSocket clients
        asyncio.create_task(
            websocket_manager.broadcast_event(message.topic, message.payload)
        )

    async def request(
        self,
        topic: str,
        payload: Dict[str, Any],
        timeout: float = 5.0,
        priority: Priority = Priority.MEDIUM
    ) -> Any:
        """
        Send a request to an agent and wait for response

        Args:
            topic: Message topic (e.g., "effects.chain.create")
            payload: Message payload
            timeout: Timeout in seconds
            priority: Message priority

        Returns:
            Response data from agent

        Raises:
            TimeoutError: If request times out
            Exception: If agent returns error
        """
        request_id = str(uuid.uuid4())

        # Add request ID and response topic to payload
        payload["request_id"] = request_id
        payload["response_topic"] = f"api.response.{request_id}"

        # Create message
        message = Message(
            topic=topic,
            sender="api",
            payload=payload,
            priority=priority
        )

        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future

        try:
            # Publish message
            self.message_bus.publish(message)
            logger.debug(f"Sent request: {topic} (ID: {request_id})")

            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)

            # Check for error in response
            if isinstance(response, dict) and "error" in response:
                raise Exception(response["error"])

            return response

        except asyncio.TimeoutError:
            logger.error(f"Request timeout: {topic} (ID: {request_id})")
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
            raise TimeoutError(f"Agent request timed out after {timeout}s")

        except Exception as e:
            logger.error(f"Request error: {topic} - {e}")
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
            raise

    def publish_event(
        self,
        topic: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.LOW
    ):
        """
        Publish an event (fire-and-forget, no response expected)

        Args:
            topic: Message topic
            payload: Message payload
            priority: Message priority
        """
        message = Message(
            topic=topic,
            sender="api",
            payload=payload,
            priority=priority
        )

        self.message_bus.publish(message)
        logger.debug(f"Published event: {topic}")


# Singleton instance
_adapter: Optional[MessageBusAdapter] = None


def get_message_bus_adapter() -> MessageBusAdapter:
    """Get singleton message bus adapter instance"""
    global _adapter
    if _adapter is None:
        _adapter = MessageBusAdapter()
    return _adapter
