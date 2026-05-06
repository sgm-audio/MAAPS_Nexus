"""
WebSocket Manager for Real-time Updates
Manages WebSocket connections and broadcasts agent events
"""

import logging
from fastapi import WebSocket
from typing import Dict, Set, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and event broadcasting
    """

    def __init__(self):
        # client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

        # topic -> Set[client_id]
        self.subscriptions: Dict[str, Set[str]] = {}

        # client_id -> Set[topics]
        self.client_subscriptions: Dict[str, Set[str]] = {}

        self.running = False

    async def start(self):
        """Start the WebSocket manager"""
        logger.info("Starting WebSocket manager...")
        self.running = True
        logger.info("WebSocket manager started")

    async def stop(self):
        """Stop the WebSocket manager"""
        logger.info("Stopping WebSocket manager...")
        self.running = False

        # Close all connections
        for client_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.close()
            except Exception:
                pass

        self.active_connections.clear()
        self.subscriptions.clear()
        self.client_subscriptions.clear()

        logger.info("WebSocket manager stopped")

    async def connect(self, websocket: WebSocket) -> str:
        """
        Accept new WebSocket connection

        Args:
            websocket: WebSocket connection

        Returns:
            client_id: Unique client identifier
        """
        await websocket.accept()
        client_id = str(uuid.uuid4())
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()

        logger.info(f"WebSocket client connected: {client_id}")
        return client_id

    def disconnect(self, client_id: str):
        """
        Disconnect client

        Args:
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # Remove from all subscriptions
        for topic_subs in self.subscriptions.values():
            topic_subs.discard(client_id)

        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]

        logger.info(f"WebSocket client disconnected: {client_id}")

    async def subscribe(self, client_id: str, topics: list):
        """
        Subscribe client to topics

        Args:
            client_id: Client identifier
            topics: List of topics to subscribe to
        """
        if client_id not in self.active_connections:
            logger.warning(f"Cannot subscribe unknown client: {client_id}")
            return

        for topic in topics:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()

            self.subscriptions[topic].add(client_id)
            self.client_subscriptions[client_id].add(topic)

        logger.debug(f"Client {client_id} subscribed to {len(topics)} topics")

        # Send confirmation
        await self.send_to_client(client_id, {
            "type": "subscribed",
            "topics": topics,
            "timestamp": datetime.now().isoformat()
        })

    async def unsubscribe(self, client_id: str, topics: list):
        """
        Unsubscribe client from topics

        Args:
            client_id: Client identifier
            topics: List of topics to unsubscribe from
        """
        for topic in topics:
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(client_id)

            if client_id in self.client_subscriptions:
                self.client_subscriptions[client_id].discard(topic)

        logger.debug(f"Client {client_id} unsubscribed from {len(topics)} topics")

        # Send confirmation
        await self.send_to_client(client_id, {
            "type": "unsubscribed",
            "topics": topics,
            "timestamp": datetime.now().isoformat()
        })

    async def handle_message(self, client_id: str, data: dict):
        """
        Handle incoming message from client

        Args:
            client_id: Client identifier
            data: Message data
        """
        message_type = data.get("type")

        if message_type == "subscribe":
            topics = data.get("topics", [])
            await self.subscribe(client_id, topics)

        elif message_type == "unsubscribe":
            topics = data.get("topics", [])
            await self.unsubscribe(client_id, topics)

        elif message_type == "ping":
            await self.send_to_client(client_id, {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })

        elif message_type == "auth":
            # Handle authentication (token validation is handled at WebSocket
            # connect-time in api.auth.validate_websocket_token).
            await self.send_to_client(client_id, {
                "type": "authenticated",
                "success": True,
                "timestamp": datetime.now().isoformat()
            })

        else:
            logger.warning(f"Unknown message type from {client_id}: {message_type}")

    async def broadcast_event(self, topic: str, data: Any):
        """
        Broadcast event to all subscribers

        Args:
            topic: Event topic
            data: Event data
        """
        if topic not in self.subscriptions:
            return

        message = {
            "type": "event",
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # Get subscribers for this topic
        subscribers = list(self.subscriptions[topic])

        # Send to all subscribers
        disconnected_clients = []
        for client_id in subscribers:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def send_to_client(self, client_id: str, message: dict):
        """
        Send message to specific client

        Args:
            client_id: Client identifier
            message: Message to send
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                self.disconnect(client_id)

    def get_stats(self) -> dict:
        """Get WebSocket manager statistics"""
        return {
            "active_connections": len(self.active_connections),
            "total_subscriptions": sum(len(subs) for subs in self.subscriptions.values()),
            "topics": len(self.subscriptions)
        }


# Singleton instance
websocket_manager = WebSocketManager()
