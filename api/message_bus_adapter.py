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
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def _ensure_bus(self):
        if self.message_bus is None:
            self.message_bus = get_message_bus()
        if not self.message_bus._running:
            self.message_bus.start()

    async def start(self):
        """Initialize and start the adapter"""
        logger.info("Starting message bus adapter...")
        self._ensure_bus()
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = None
        self.running = True

        # Subscribe to response topics
        self.message_bus.subscribe(
            "api.response.*", "api_adapter", self._handle_response
        )

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
            "system.agent.error",
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
        from api.websocket import websocket_manager

        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                websocket_manager.broadcast_event(message.topic, message.payload),
                self.loop,
            )

    async def request(
        self,
        topic: str,
        payload: Dict[str, Any],
        timeout: float = 5.0,
        priority: Priority = Priority.MEDIUM,
    ) -> Any:
        """
        Send a request to an agent and wait for response
        """
        self._ensure_bus()
        request_id = str(uuid.uuid4())
        req_payload = dict(payload) if payload else {}
        req_payload.setdefault("request_id", request_id)

        message = Message(
            topic=topic,
            sender="api",
            payload=req_payload,
            correlation_id=request_id,
            priority=priority,
        )

        response_msg = await asyncio.to_thread(
            self.message_bus.request, message, timeout
        )
        if response_msg is None:
            logger.error(f"Request timeout: {topic} (ID: {request_id})")
            raise TimeoutError(f"Agent request timed out after {timeout}s")

        response = response_msg.payload
        if (
            isinstance(response, dict)
            and response.get("success") is False
            and "error" in response
        ):
            raise Exception(response["error"])

        return response

    def publish_event(
        self, topic: str, payload: Dict[str, Any], priority: Priority = Priority.LOW
    ):
        """
        Publish an event (fire-and-forget, no response expected)
        """
        self._ensure_bus()
        message = Message(topic=topic, sender="api", payload=payload, priority=priority)

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
