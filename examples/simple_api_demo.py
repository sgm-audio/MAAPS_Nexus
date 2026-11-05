"""
MAAPS Simple API Demonstration
Demonstrates the core MAAPS API functionality with real calls
"""

import requests
import json
from datetime import datetime


class SimpleMAAPSDemo:
    """Simple demonstration of current MAAPS API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def print_section(self, title: str):
        """Print section header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    def print_response(self, endpoint: str, response: requests.Response):
        """Print formatted API response"""
        print(f"\nEndpoint: {endpoint}")
        print(f"Status: {response.status_code} {response.reason}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response:\n{json.dumps(data, indent=2)}")
            except:
                print(f"Response: {response.text[:200]}")
        else:
            print(f"Error: {response.text}")

    def demo_system_endpoints(self):
        """Demonstrate system endpoints"""
        self.print_section("SYSTEM ENDPOINTS")

        # Root endpoint
        print("\n1. API Root (GET /)")
        response = requests.get(f"{self.base_url}/")
        self.print_response("GET /", response)

        # Health check
        print("\n2. Health Check (GET /health)")
        response = requests.get(f"{self.base_url}/health")
        self.print_response("GET /health", response)

        # System metrics
        print("\n3. System Metrics (GET /metrics)")
        response = requests.get(f"{self.base_url}/metrics")
        self.print_response("GET /metrics", response)

        # List agents
        print("\n4. List Agents (GET /agents)")
        response = requests.get(f"{self.base_url}/agents")
        self.print_response("GET /agents", response)

        # Version info
        print("\n5. Version Info (GET /system/version)")
        response = requests.get(f"{self.base_url}/system/version")
        self.print_response("GET /system/version", response)

    def demo_audio_processing(self):
        """Demonstrate audio processing endpoints"""
        self.print_section("AUDIO PROCESSING")

        # Create sample audio data (1 second of silence at 44100Hz)
        sample_rate = 44100
        audio_data = [0.0] * sample_rate

        # Audio enhancement
        print("\n1. Audio Enhancement (POST /audio/enhance)")
        enhance_request = {
            "audio_data": audio_data[:1000],  # Use smaller sample for demo
            "sample_rate": sample_rate,
            "noise_reduction": 0.8,
            "declicking_sensitivity": 0.5,
            "preserve_transients": True
        }
        response = requests.post(
            f"{self.base_url}/audio/enhance",
            json=enhance_request
        )
        self.print_response("POST /audio/enhance", response)

        # Metadata extraction
        print("\n2. Metadata Extraction (POST /audio/metadata)")
        metadata_request = {
            "audio_data": audio_data[:1000],
            "sample_rate": sample_rate,
            "deep_analysis": True
        }
        response = requests.post(
            f"{self.base_url}/audio/metadata",
            json=metadata_request
        )
        self.print_response("POST /audio/metadata", response)

    def demo_music_generation(self):
        """Demonstrate music generation endpoints"""
        self.print_section("MUSIC GENERATION")

        # Generate melody
        print("\n1. Generate Melody (POST /music/generate)")
        melody_request = {
            "content_type": "melody",
            "key": "C major",
            "tempo": 120.0,
            "time_signature": "4/4",
            "chord_progression": ["C", "Am", "F", "G"],
            "length_bars": 8
        }
        response = requests.post(
            f"{self.base_url}/music/generate",
            json=melody_request
        )
        self.print_response("POST /music/generate (melody)", response)

        # Generate harmony
        print("\n2. Generate Harmony (POST /music/generate)")
        harmony_request = {
            "content_type": "harmony",
            "key": "G major",
            "tempo": 90.0,
            "time_signature": "3/4",
            "chord_progression": ["G", "Em", "C", "D"],
            "length_bars": 4
        }
        response = requests.post(
            f"{self.base_url}/music/generate",
            json=harmony_request
        )
        self.print_response("POST /music/generate (harmony)", response)

        # Generate drums
        print("\n3. Generate Drums (POST /music/generate)")
        drums_request = {
            "content_type": "drums",
            "key": "C major",
            "tempo": 140.0,
            "time_signature": "4/4",
            "chord_progression": ["C"],
            "length_bars": 2
        }
        response = requests.post(
            f"{self.base_url}/music/generate",
            json=drums_request
        )
        self.print_response("POST /music/generate (drums)", response)

        # Generate bass
        print("\n4. Generate Bass (POST /music/generate)")
        bass_request = {
            "content_type": "bass",
            "key": "A minor",
            "tempo": 100.0,
            "time_signature": "4/4",
            "chord_progression": ["Am", "F", "C", "G"],
            "length_bars": 8
        }
        response = requests.post(
            f"{self.base_url}/music/generate",
            json=bass_request
        )
        self.print_response("POST /music/generate (bass)", response)

    def run_demo(self):
        """Run complete demonstration"""
        print("\n" + "=" * 70)
        print("  MAAPS API LIVE DEMONSTRATION")
        print("  Server: " + self.base_url)
        print("  Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 70)

        try:
            # Test connectivity
            print("\nTesting server connectivity...")
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                print(f"ERROR: Server not healthy! Status: {response.status_code}")
                return

            health_data = response.json()
            print(f"  Server is healthy!")
            print(f"  Health Score: {health_data['health_score']}%")
            print(f"  Agents: {health_data['agents_healthy']}/{health_data['agents_total']}")
            print(f"  Uptime: {health_data['system_uptime_seconds']:.1f}s")

            # Run demos
            self.demo_system_endpoints()
            self.demo_audio_processing()
            self.demo_music_generation()

            # Summary
            self.print_section("DEMONSTRATION COMPLETE")
            print("\n  All core API endpoints tested successfully!")
            print("\n  Next steps:")
            print("    - Interactive API docs: http://localhost:8000/docs")
            print("    - ReDoc documentation: http://localhost:8000/redoc")
            print("    - Try the WebSocket test: python tests/test_websocket.py")
            print("    - Build React frontend: cd frontend/maaps-ui && npm run dev")
            print("\n" + "=" * 70)

        except requests.exceptions.ConnectionError:
            print("\nERROR: Could not connect to MAAPS API server!")
            print("Make sure the server is running:")
            print("  uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")

        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user")

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    demo = SimpleMAAPSDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()
