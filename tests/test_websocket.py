"""
MAAPS WebSocket Test Client
Demonstrates real-time event streaming and subscriptions
"""

import asyncio
import os
import pytest
import websockets
import json
from datetime import datetime
from typing import Set

DEFAULT_WS_URL = os.getenv("MAAPS_WS_URL", "ws://127.0.0.1:18000/ws")

class WebSocketTestClient:
    """WebSocket test client for MAAPS API"""

    def __init__(self, url: str = DEFAULT_WS_URL):
        self.url = url
        self.ws = None
        self.subscriptions: Set[str] = set()

    async def connect(self):
        """Connect to WebSocket server"""
        print(f"[{self._timestamp()}] Connecting to {self.url}...")
        try:
            self.ws = await websockets.connect(self.url)
            print(f"[{self._timestamp()}] Connected successfully!")
            return True
        except Exception as e:
            print(f"[{self._timestamp()}] Connection failed: {e}")
            return False

    async def subscribe(self, topics: list[str]):
        """Subscribe to event topics"""
        if not self.ws:
            print("Not connected!")
            return

        self.subscriptions.update(topics)
        message = {
            "type": "subscribe",
            "topics": topics
        }

        print(f"\n[{self._timestamp()}] Subscribing to topics:")
        for topic in topics:
            print(f"  - {topic}")

        await self.ws.send(json.dumps(message))
        print(f"[{self._timestamp()}] Subscription request sent")

    async def listen(self, duration: int = 30):
        """Listen for events for specified duration"""
        if not self.ws:
            print("Not connected!")
            return

        print(f"\n[{self._timestamp()}] Listening for events (duration: {duration}s)...")
        print("=" * 60)

        try:
            end_time = asyncio.get_event_loop().time() + duration

            while asyncio.get_event_loop().time() < end_time:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                    self._handle_message(message)
                except asyncio.TimeoutError:
                    # No message received, continue
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print(f"\n[{self._timestamp()}] Connection closed by server")
                    break

        except KeyboardInterrupt:
            print(f"\n[{self._timestamp()}] Interrupted by user")

        print("=" * 60)
        print(f"[{self._timestamp()}] Stopped listening")

    def _handle_message(self, message: str):
        """Handle received message"""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "unknown")

            if msg_type == "event":
                topic = data.get("topic", "unknown")
                timestamp = data.get("timestamp", "")
                event_data = data.get("data", {})

                print(f"\n[{self._timestamp()}] EVENT RECEIVED")
                print(f"  Topic: {topic}")
                print(f"  Server Time: {timestamp}")
                print(f"  Data: {json.dumps(event_data, indent=4)}")

            elif msg_type == "subscribed":
                topics = data.get("topics", [])
                print(f"\n[{self._timestamp()}] SUBSCRIPTION CONFIRMED")
                print(f"  Topics: {', '.join(topics)}")

            elif msg_type == "error":
                error = data.get("message", "Unknown error")
                print(f"\n[{self._timestamp()}] ERROR")
                print(f"  Message: {error}")

            else:
                print(f"\n[{self._timestamp()}] UNKNOWN MESSAGE TYPE: {msg_type}")
                print(f"  Data: {json.dumps(data, indent=2)}")

        except json.JSONDecodeError as e:
            print(f"\n[{self._timestamp()}] Failed to parse message: {e}")
            print(f"  Raw: {message}")

    async def disconnect(self):
        """Disconnect from server"""
        if self.ws:
            await self.ws.close()
            print(f"\n[{self._timestamp()}] Disconnected")

    @staticmethod
    def _timestamp() -> str:
        """Get formatted timestamp"""
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]


@pytest.mark.asyncio
async def test_effects_events():
    """Test effects chain parameter change events"""
    client = WebSocketTestClient()

    assert await client.connect()
    await client.subscribe([
        "effects.parameter.change",
        "effects.chain.created",
        "effects.bypass.toggled"
    ])
    await client.listen(duration=1)
    await client.disconnect()


@pytest.mark.asyncio
async def test_looping_events():
    """Test live looping events"""
    client = WebSocketTestClient()

    assert await client.connect()
    await client.subscribe([
        "loop.record.started",
        "loop.record.stopped",
        "loop.playback.started",
        "loop.playback.stopped"
    ])
    await client.listen(duration=1)
    await client.disconnect()


@pytest.mark.asyncio
async def test_sync_events():
    """Test sync/clock events"""
    client = WebSocketTestClient()

    assert await client.connect()
    await client.subscribe([
        "sync.tempo.changed",
        "sync.clock.position",
        "sync.transport.changed"
    ])
    await client.listen(duration=1)
    await client.disconnect()


@pytest.mark.asyncio
async def test_all_events():
    """Subscribe to all event topics"""
    client = WebSocketTestClient()

    assert await client.connect()
    all_topics = [
        "effects.parameter.change",
        "effects.chain.created",
        "loop.record.started",
        "loop.record.stopped",
        "sync.clock.position",
        "automation.scene.recalled",
        "system.health.changed",
    ]
    await client.subscribe(all_topics)
    await client.listen(duration=1)
    await client.disconnect()


async def main():
    """Run all WebSocket tests"""
    print("\n" + "=" * 60)
    print("MAAPS WebSocket Test Client")
    print("=" * 60)
    print("\nThis script tests real-time event streaming from the MAAPS API.")
    print("Make sure the API server is running on http://localhost:8000")
    print("\nTests will run sequentially. Use Ctrl+C to skip a test.")

    try:
        # Run individual tests
        await test_effects_events()
        await asyncio.sleep(2)

        await test_looping_events()
        await asyncio.sleep(2)

        await test_sync_events()
        await asyncio.sleep(2)

        # Final comprehensive test
        await test_all_events()

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")

    print("\n" + "=" * 60)
    print("All WebSocket tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nStarting WebSocket tests in 3 seconds...")
    print("(Press Ctrl+C to cancel)")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
