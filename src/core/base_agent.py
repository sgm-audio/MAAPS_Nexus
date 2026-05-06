"""
Base agent class for the multi-agent system.
Provides common functionality for all agents including communication,
lifecycle management, and monitoring.
"""

import threading
import time
import logging
from abc import ABC
from typing import List, Optional, Dict, Any
from enum import Enum

from .message_bus import get_message_bus, MessageBus
from .message_types import Message, Priority, Topics, SystemEvent, LogEntry


logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent lifecycle states"""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class AgentCapability(Enum):
    """Declared capabilities for agents in the multi-agent audio system."""
    AUDIO_ANALYSIS = "audio_analysis"
    AUDIO_PROCESSING = "audio_processing"
    MACHINE_LEARNING = "machine_learning"
    COORDINATION = "coordination"
    DAW_INTEGRATION = "daw_integration"
    MONITORING = "monitoring"


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Handles communication, lifecycle, and common functionality.
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: Optional[str] = None,
        agent_type: Optional[str] = None,
        capabilities: Optional[List["AgentCapability"]] = None,
        message_bus: Optional[MessageBus] = None,
    ):
        """
        Initialize the agent.

        Args:
            agent_id: Unique identifier for this agent.
            agent_name: Human-readable agent name. Defaults to agent_id.
            agent_type: Logical type ("critic", "eq", "dynamics", "hgo", ...).
            capabilities: Declared capabilities (see AgentCapability).
            message_bus: Optional message bus override. Falls back to the
                process-wide singleton if not provided.
        """
        self.agent_id = agent_id
        self.agent_name = agent_name or agent_id
        self.agent_type = agent_type
        self.capabilities = list(capabilities or [])

        # State management
        self._state = AgentState.CREATED
        self._state_lock = threading.Lock()

        # Message bus — accept an injected bus for testing; fall back to singleton
        if message_bus is not None:
            self._message_bus = message_bus
        else:
            self._message_bus = get_message_bus()
        # Public alias used by the multi-agent core
        self.message_bus = self._message_bus

        # Subscription management
        self._subscribed_topics: List[str] = []

        # Heartbeat thread
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_interval = 1.0  # seconds

        # Metrics
        self._metrics = {
            "messages_received": 0,
            "messages_sent": 0,
            "errors": 0,
            "uptime_seconds": 0.0,
            "start_time": None
        }
        self._metrics_lock = threading.Lock()

        logger.info(f"Agent {self.agent_id} ({self.agent_name}) created")

    def setup(self):
        """Optional lifecycle hook. Override to subscribe to topics, etc."""
        return None

    def teardown(self):
        """Optional lifecycle hook. Override for resource cleanup."""
        return None

    def handle_message(self, message: Message):
        """Default no-op message handler. Override for real behavior."""
        return None

    # ---- Compatibility re-declarations (non-abstract) ----
    # The original BaseAgent declared these as abstract. We keep the
    # method names available so subclasses can still override them, but
    # we no longer prevent instantiation when they are not overridden.
    def _abstract_setup_placeholder(self):
        pass

    def start(self):
        """Start the agent"""
        with self._state_lock:
            if self._state != AgentState.CREATED:
                logger.warning(f"Agent {self.agent_id} already started or in invalid state")
                return

            self._state = AgentState.STARTING

        try:
            # Record start time
            with self._metrics_lock:
                self._metrics["start_time"] = time.time()

            # Call agent-specific setup
            self.setup()

            # Start heartbeat
            self._start_heartbeat()

            # Update state
            with self._state_lock:
                self._state = AgentState.RUNNING

            # Publish agent started event
            self._publish_system_event(
                Topics.SYSTEM_AGENT_STARTED,
                {"agent_id": self.agent_id, "agent_name": self.agent_name}
            )

            logger.info(f"Agent {self.agent_id} started")

        except Exception as e:
            with self._state_lock:
                self._state = AgentState.ERROR

            logger.error(f"Error starting agent {self.agent_id}: {e}")
            raise

    def stop(self):
        """Stop the agent"""
        with self._state_lock:
            if self._state not in [AgentState.RUNNING, AgentState.ERROR]:
                return

            self._state = AgentState.STOPPING

        try:
            # Stop heartbeat
            self._stop_heartbeat()

            # Unsubscribe from all topics
            for topic in self._subscribed_topics[:]:
                self.unsubscribe(topic)

            # Call agent-specific teardown
            self.teardown()

            # Update state
            with self._state_lock:
                self._state = AgentState.STOPPED

            # Publish agent stopped event
            self._publish_system_event(
                Topics.SYSTEM_AGENT_STOPPED,
                {"agent_id": self.agent_id, "agent_name": self.agent_name}
            )

            logger.info(f"Agent {self.agent_id} stopped")

        except Exception as e:
            logger.error(f"Error stopping agent {self.agent_id}: {e}")
            with self._state_lock:
                self._state = AgentState.ERROR
            raise

    def subscribe(self, topic: str):
        """
        Subscribe to a topic.

        Args:
            topic: Topic to subscribe to (supports wildcards)
        """
        self._message_bus.subscribe(topic, self.agent_id, self._on_message_received)
        self._subscribed_topics.append(topic)
        logger.debug(f"Agent {self.agent_id} subscribed to {topic}")

    def unsubscribe(self, topic: str):
        """
        Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from
        """
        self._message_bus.unsubscribe(topic, self.agent_id)
        if topic in self._subscribed_topics:
            self._subscribed_topics.remove(topic)
        logger.debug(f"Agent {self.agent_id} unsubscribed from {topic}")

    def publish(self, topic: str, payload: Dict[str, Any], priority: Priority = Priority.MEDIUM) -> bool:
        """
        Publish a message.

        Args:
            topic: Topic to publish to
            payload: Message payload
            priority: Message priority

        Returns:
            True if message was published successfully
        """
        message = Message(
            topic=topic,
            sender=self.agent_id,
            payload=payload,
            priority=priority
        )

        success = self._message_bus.publish(message)

        if success:
            with self._metrics_lock:
                self._metrics["messages_sent"] += 1

        return success

    def request(self, topic: str, payload: Dict[str, Any],
                timeout: float = 5.0, priority: Priority = Priority.MEDIUM) -> Optional[Message]:
        """
        Send a request and wait for response.

        Args:
            topic: Topic to send request to
            payload: Request payload
            timeout: Maximum wait time for response
            priority: Message priority

        Returns:
            Response message or None if timeout
        """
        message = Message(
            topic=topic,
            sender=self.agent_id,
            payload=payload,
            priority=priority
        )

        response = self._message_bus.request(message, timeout)

        if response:
            with self._metrics_lock:
                self._metrics["messages_sent"] += 1
                self._metrics["messages_received"] += 1

        return response

    def respond(self, original_message: Message, response_payload: Dict[str, Any]) -> bool:
        """
        Send a response to a request.

        Args:
            original_message: The original request message
            response_payload: Response data

        Returns:
            True if response was sent
        """
        return self._message_bus.respond(original_message, response_payload)

    def log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Log a message.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            context: Additional context data
        """
        log_entry = LogEntry(
            level=level,
            agent_id=self.agent_id,
            message=message,
            context=context or {},
            metrics=self.get_metrics()
        )

        # Publish to logging topic
        topic_map = {
            "INFO": Topics.LOG_EVENT_INFO,
            "WARNING": Topics.LOG_EVENT_WARNING,
            "ERROR": Topics.LOG_EVENT_ERROR
        }

        topic = topic_map.get(level, Topics.LOG_EVENT_INFO)
        self.publish(topic, log_entry.__dict__, priority=Priority.LOW)

        # Also log locally
        logger.log(
            getattr(logging, level),
            f"[{self.agent_id}] {message}",
            extra={"context": context}
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current agent metrics"""
        with self._metrics_lock:
            metrics = self._metrics.copy()

        # Calculate uptime
        if metrics["start_time"]:
            metrics["uptime_seconds"] = time.time() - metrics["start_time"]

        # Add state
        metrics["state"] = self._state.value

        return metrics

    def get_state(self) -> AgentState:
        """Get current agent state"""
        with self._state_lock:
            return self._state

    def _on_message_received(self, message: Message):
        """
        Internal message handler.
        Called by message bus when a message is received.

        Args:
            message: Received message
        """
        try:
            with self._metrics_lock:
                self._metrics["messages_received"] += 1

            # Call agent-specific handler
            self.handle_message(message)

        except Exception as e:
            with self._metrics_lock:
                self._metrics["errors"] += 1

            logger.error(f"Error handling message in agent {self.agent_id}: {e}")

            # Publish error event
            self._publish_system_event(
                Topics.SYSTEM_ERROR_CRITICAL,
                {
                    "agent_id": self.agent_id,
                    "error": str(e),
                    "message_id": message.message_id,
                    "topic": message.topic
                },
                severity="error"
            )

    def _publish_system_event(self, topic: str, data: Dict[str, Any], severity: str = "info"):
        """
        Publish a system event.

        Args:
            topic: Event topic
            data: Event data
            severity: Event severity
        """
        event = SystemEvent(
            event_type=topic,
            agent_id=self.agent_id,
            severity=severity,
            data=data
        )

        self.publish(topic, event.__dict__, priority=Priority.HIGH)

    def _start_heartbeat(self):
        """Start the heartbeat thread"""
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"{self.agent_id}_heartbeat",
            daemon=True
        )
        self._heartbeat_thread.start()

    def _stop_heartbeat(self):
        """Stop the heartbeat thread"""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            # Thread will exit when state changes
            self._heartbeat_thread.join(timeout=2.0)

    def _heartbeat_loop(self):
        """Heartbeat loop - runs in separate thread"""
        while self.get_state() == AgentState.RUNNING:
            try:
                self._publish_system_event(
                    Topics.SYSTEM_HEARTBEAT,
                    {"agent_id": self.agent_id, "metrics": self.get_metrics()},
                    severity="info"
                )
            except Exception as e:
                logger.error(f"Error sending heartbeat from {self.agent_id}: {e}")

            time.sleep(self._heartbeat_interval)


class AgentRegistry:
    """Registry for managing all agents in the system"""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._lock = threading.Lock()

    def register(self, agent: BaseAgent):
        """Register an agent"""
        with self._lock:
            if agent.agent_id in self._agents:
                raise ValueError(f"Agent {agent.agent_id} already registered")
            self._agents[agent.agent_id] = agent
            logger.info(f"Registered agent {agent.agent_id}")

    def unregister(self, agent_id: str):
        """Unregister an agent"""
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                logger.info(f"Unregistered agent {agent_id}")

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID"""
        with self._lock:
            return self._agents.get(agent_id)

    def get_all(self) -> List[BaseAgent]:
        """Get all registered agents"""
        with self._lock:
            return list(self._agents.values())

    def start_all(self):
        """Start all registered agents"""
        with self._lock:
            for agent in self._agents.values():
                try:
                    agent.start()
                except Exception as e:
                    logger.error(f"Error starting agent {agent.agent_id}: {e}")

    def stop_all(self):
        """Stop all registered agents"""
        with self._lock:
            for agent in self._agents.values():
                try:
                    agent.stop()
                except Exception as e:
                    logger.error(f"Error stopping agent {agent.agent_id}: {e}")


# Global agent registry
_global_registry: Optional[AgentRegistry] = None
_registry_lock = threading.Lock()


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry instance (singleton)"""
    global _global_registry

    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = AgentRegistry()

    return _global_registry
