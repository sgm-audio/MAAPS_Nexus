"""
MAAPS WebSocket Test Client
Demonstrates real-time event streaming and subscriptions
"""

import asyncio
import websockets
import json
from datetime import datetime
from typing import Set

class WebSocketTestClient:
    """WebSocket test client for MAAPS API"""

    def __init__(self, url: str = "ws://localhost:8000/ws"):
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


async def test_effects_events():
    """Test effects chain parameter change events"""
    print("\n" + "=" * 60)
    print("TEST 1: Effects Chain Parameter Changes")
    print("=" * 60)

    client = WebSocketTestClient()

    if await client.connect():
        await client.subscribe([
            "effects.parameter.change",
            "effects.chain.created",
            "effects.bypass.toggled"
        ])

        print("\nWaiting for effects events...")
        print("(Manually trigger parameter changes in the API to see events)")

        await client.listen(duration=15)
        await client.disconnect()


async def test_looping_events():
    """Test live looping events"""
    print("\n" + "=" * 60)
    print("TEST 2: Live Looping Events")
    print("=" * 60)

    client = WebSocketTestClient()

    if await client.connect():
        await client.subscribe([
            "loop.record.started",
            "loop.record.stopped",
            "loop.playback.started",
            "loop.playback.stopped"
        ])

        print("\nWaiting for looping events...")
        print("(Manually trigger loop recording in the API to see events)")

        await client.listen(duration=15)
        await client.disconnect()


async def test_sync_events():
    """Test sync/clock events"""
    print("\n" + "=" * 60)
    print("TEST 3: Sync & Clock Events")
    print("=" * 60)

    client = WebSocketTestClient()

    if await client.connect():
        await client.subscribe([
            "sync.tempo.changed",
            "sync.clock.position",
            "sync.transport.changed"
        ])

        print("\nWaiting for sync events...")
        print("(Manually change tempo or transport in the API to see events)")

        await client.listen(duration=15)
        await client.disconnect()


async def test_all_events():
    """Subscribe to all event topics"""
    print("\n" + "=" * 60)
    print("TEST 4: All Events (Comprehensive)")
    print("=" * 60)

    client = WebSocketTestClient()

    if await client.connect():
        # Subscribe to all major event topics
        all_topics = [
            # Effects
            "effects.parameter.change",
            "effects.chain.created",
            "effects.chain.deleted",
            "effects.bypass.toggled",
            # Looping
            "loop.record.started",
            "loop.record.stopped",
            "loop.playback.started",
            "loop.playback.stopped",
            "loop.overdub.started",
            "loop.cleared",
            # Sync
            "sync.tempo.changed",
            "sync.time_signature.changed",
            "sync.clock.position",
            "sync.transport.changed",
            # Automation
            "automation.recording.started",
            "automation.recording.stopped",
            "automation.scene.recalled",
            "automation.macro.triggered",
            # System
            "system.health.changed",
            "system.agent.status",
        ]

        await client.subscribe(all_topics)

        print("\nListening for ALL events...")
        print("(Trigger any API action to see corresponding events)")

        await client.listen(duration=30)
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
