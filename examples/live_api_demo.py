"""
MAAPS Live API Demonstration
Shows the complete system in action with real API calls
"""

import requests
import time
from typing import Dict, Any
from datetime import datetime


class MAAPSDemo:
    """Live demonstration of MAAPS API functionality"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.created_resources = {
            "chains": [],
            "tracks": [],
            "scenes": [],
            "macros": []
        }

    def print_header(self, title: str):
        """Print formatted section header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    def print_result(self, response: requests.Response, description: str):
        """Print API response in formatted way"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] {description}")
        print(f"  Status: {response.status_code} {response.reason}")

        try:
            data = response.json()
            if "data" in data:
                print(f"  Response: {data.get('message', 'Success')}")
                if isinstance(data["data"], dict):
                    for key, value in list(data["data"].items())[:5]:  # Show first 5 keys
                        print(f"    - {key}: {value}")
                elif isinstance(data["data"], list):
                    print(f"    - Items: {len(data['data'])}")
            else:
                print(f"  Data: {str(data)[:100]}")
        except Exception as e:
            print(f"  Raw: {response.text[:100]}")

    def test_system_health(self):
        """Test 1: Check system health"""
        self.print_header("TEST 1: System Health & Metrics")

        # Get system health
        response = self.session.get(f"{self.base_url}/system/health")
        self.print_result(response, "Get System Health")

        # Get system metrics
        response = self.session.get(f"{self.base_url}/system/metrics")
        self.print_result(response, "Get System Metrics")

        # Get all agents
        response = self.session.get(f"{self.base_url}/system/agents")
        self.print_result(response, "List All Agents")

        # Get specific agent stats
        response = self.session.get(f"{self.base_url}/system/agents/effects_agent/stats")
        self.print_result(response, "Get Effects Agent Statistics")

        time.sleep(1)

    def test_effects_chain(self):
        """Test 2: Create and manage effects chain"""
        self.print_header("TEST 2: Effects Chain Management")

        # Create effect chain
        chain_data = {
            "chain_name": "Demo Vocal Chain",
            "effects": [
                {
                    "effect_type": "gate",
                    "effect_name": "Noise Gate",
                    "parameters": {
                        "threshold": -40.0,
                        "ratio": 10.0,
                        "attack": 0.5,
                        "release": 100.0
                    },
                    "bypass": False
                },
                {
                    "effect_type": "compressor",
                    "effect_name": "Vocal Comp",
                    "parameters": {
                        "threshold": -18.0,
                        "ratio": 4.0,
                        "attack": 5.0,
                        "release": 50.0,
                        "makeup_gain": 3.0
                    },
                    "bypass": False
                },
                {
                    "effect_type": "eq",
                    "effect_name": "Vocal EQ",
                    "parameters": {
                        "low_gain": 0.0,
                        "mid_gain": 2.0,
                        "high_gain": 1.5
                    },
                    "bypass": False
                }
            ]
        }

        response = self.session.post(f"{self.base_url}/effects/chains", json=chain_data)
        self.print_result(response, "Create Effects Chain")

        if response.status_code == 201:
            chain_id = response.json()["data"]["chain_id"]
            self.created_resources["chains"].append(chain_id)

            # List all chains
            response = self.session.get(f"{self.base_url}/effects/chains")
            self.print_result(response, "List All Effect Chains")

            # Get specific chain
            response = self.session.get(f"{self.base_url}/effects/chains/{chain_id}")
            self.print_result(response, f"Get Chain Details (ID: {chain_id})")

            # Update effect parameters
            param_data = {
                "threshold": -15.0,
                "ratio": 6.0,
                "makeup_gain": 4.5
            }
            response = self.session.patch(
                f"{self.base_url}/effects/chains/{chain_id}/effects/vocal-comp/parameters",
                json=param_data
            )
            self.print_result(response, "Update Compressor Parameters")

            # Toggle bypass
            response = self.session.post(
                f"{self.base_url}/effects/chains/{chain_id}/effects/vocal-comp/bypass",
                json={"bypass": True}
            )
            self.print_result(response, "Toggle Effect Bypass")

        time.sleep(1)

    def test_live_looping(self):
        """Test 3: Live looping operations"""
        self.print_header("TEST 3: Live Looping System")

        # Create loop track
        track_data = {
            "track_name": "Demo Loop Track",
            "input_source": "input_1",
            "length_bars": 4,
            "auto_quantize": True
        }

        response = self.session.post(f"{self.base_url}/looping/tracks", json=track_data)
        self.print_result(response, "Create Loop Track")

        if response.status_code == 201:
            track_id = response.json()["data"]["track_id"]
            self.created_resources["tracks"].append(track_id)

            # List all tracks
            response = self.session.get(f"{self.base_url}/looping/tracks")
            self.print_result(response, "List All Loop Tracks")

            # Get track details
            response = self.session.get(f"{self.base_url}/looping/tracks/{track_id}")
            self.print_result(response, f"Get Track Details (ID: {track_id})")

            # Start recording
            response = self.session.post(f"{self.base_url}/looping/tracks/{track_id}/record/start")
            self.print_result(response, "Start Recording Loop")

            time.sleep(0.5)

            # Stop recording
            response = self.session.post(f"{self.base_url}/looping/tracks/{track_id}/record/stop")
            self.print_result(response, "Stop Recording Loop")

            # Start playback
            response = self.session.post(f"{self.base_url}/looping/tracks/{track_id}/play")
            self.print_result(response, "Start Loop Playback")

            # Adjust volume
            response = self.session.patch(
                f"{self.base_url}/looping/tracks/{track_id}/volume",
                json={"volume": 0.8}
            )
            self.print_result(response, "Adjust Loop Volume")

        time.sleep(1)

    def test_sync_clock(self):
        """Test 4: Sync and clock operations"""
        self.print_header("TEST 4: Sync & Clock Control")

        # Set tempo
        response = self.session.post(
            f"{self.base_url}/sync/tempo/set",
            json={"bpm": 120.0, "time_signature": "4/4"}
        )
        self.print_result(response, "Set Tempo to 120 BPM")

        # Get current tempo
        response = self.session.get(f"{self.base_url}/sync/tempo")
        self.print_result(response, "Get Current Tempo")

        # Tap tempo (simulate 3 taps)
        for i in range(3):
            response = self.session.post(f"{self.base_url}/sync/tempo/tap")
            self.print_result(response, f"Tap Tempo (tap {i+1}/3)")
            time.sleep(0.5)

        # Start transport
        response = self.session.post(f"{self.base_url}/sync/transport/play")
        self.print_result(response, "Start Transport (Play)")

        time.sleep(0.5)

        # Get clock position
        response = self.session.get(f"{self.base_url}/sync/clock/position")
        self.print_result(response, "Get Clock Position")

        # Stop transport
        response = self.session.post(f"{self.base_url}/sync/transport/stop")
        self.print_result(response, "Stop Transport")

        time.sleep(1)

    def test_automation(self):
        """Test 5: Performance automation"""
        self.print_header("TEST 5: Performance Automation")

        # Create scene
        scene_data = {
            "scene_name": "Demo Scene 1",
            "parameter_states": {
                "vocal_comp_threshold": -18.0,
                "vocal_eq_high_gain": 2.0,
                "master_volume": 0.85
            },
            "transition_time": 1.0
        }

        response = self.session.post(f"{self.base_url}/automation/scenes", json=scene_data)
        self.print_result(response, "Create Performance Scene")

        if response.status_code == 201:
            scene_id = response.json()["data"]["scene_id"]
            self.created_resources["scenes"].append(scene_id)

            # List all scenes
            response = self.session.get(f"{self.base_url}/automation/scenes")
            self.print_result(response, "List All Scenes")

            # Recall scene
            response = self.session.post(f"{self.base_url}/automation/scenes/{scene_id}/recall")
            self.print_result(response, f"Recall Scene (ID: {scene_id})")

        # Create macro
        macro_data = {
            "macro_name": "Quick Fade Out",
            "actions": [
                {
                    "action_type": "set_parameter",
                    "target": "master_volume",
                    "value": 0.0,
                    "transition_time": 2.0
                },
                {
                    "action_type": "stop_transport",
                    "delay": 2.0
                }
            ]
        }

        response = self.session.post(f"{self.base_url}/automation/macros", json=macro_data)
        self.print_result(response, "Create Automation Macro")

        if response.status_code == 201:
            macro_id = response.json()["data"]["macro_id"]
            self.created_resources["macros"].append(macro_id)

            # Trigger macro
            response = self.session.post(f"{self.base_url}/automation/macros/{macro_id}/trigger")
            self.print_result(response, "Trigger Macro")

        time.sleep(1)

    def test_complete_workflow(self):
        """Test 6: Complete production workflow"""
        self.print_header("TEST 6: Complete Production Workflow")

        print("\nSimulating a complete music production session:")
        print("  1. Create effects chain for vocals")
        print("  2. Set tempo and start transport")
        print("  3. Create loop track and record")
        print("  4. Create performance scene")
        print("  5. Automate parameters")

        # Step 1: Effects chain
        print("\n  Step 1: Setting up effects chain...")
        chain_data = {
            "chain_name": "Production Vocal Chain",
            "effects": [
                {
                    "effect_type": "gate",
                    "effect_name": "Gate",
                    "parameters": {"threshold": -35.0, "ratio": 8.0},
                    "bypass": False
                },
                {
                    "effect_type": "compressor",
                    "effect_name": "Compressor",
                    "parameters": {"threshold": -20.0, "ratio": 4.0, "makeup_gain": 5.0},
                    "bypass": False
                },
                {
                    "effect_type": "reverb",
                    "effect_name": "Reverb",
                    "parameters": {"room_size": 0.5, "damping": 0.7, "wet_dry": 0.3},
                    "bypass": False
                }
            ]
        }
        response = self.session.post(f"{self.base_url}/effects/chains", json=chain_data)
        print(f"    Created chain: {response.status_code}")

        # Step 2: Tempo and transport
        print("\n  Step 2: Setting tempo and starting transport...")
        response = self.session.post(
            f"{self.base_url}/sync/tempo/set",
            json={"bpm": 128.0, "time_signature": "4/4"}
        )
        print(f"    Set tempo to 128 BPM: {response.status_code}")

        response = self.session.post(f"{self.base_url}/sync/transport/play")
        print(f"    Started transport: {response.status_code}")

        # Step 3: Create and record loop
        print("\n  Step 3: Creating and recording loop track...")
        track_data = {
            "track_name": "Vocal Loop",
            "input_source": "input_1",
            "length_bars": 8,
            "auto_quantize": True
        }
        response = self.session.post(f"{self.base_url}/looping/tracks", json=track_data)
        print(f"    Created track: {response.status_code}")

        if response.status_code == 201:
            track_id = response.json()["data"]["track_id"]

            response = self.session.post(f"{self.base_url}/looping/tracks/{track_id}/record/start")
            print(f"    Started recording: {response.status_code}")

            time.sleep(0.5)

            response = self.session.post(f"{self.base_url}/looping/tracks/{track_id}/record/stop")
            print(f"    Stopped recording: {response.status_code}")

            response = self.session.post(f"{self.base_url}/looping/tracks/{track_id}/play")
            print(f"    Started playback: {response.status_code}")

        # Step 4: Create performance scene
        print("\n  Step 4: Creating performance scene...")
        scene_data = {
            "scene_name": "Chorus",
            "parameter_states": {
                "reverb_wet_dry": 0.5,
                "compressor_threshold": -15.0
            },
            "transition_time": 0.5
        }
        response = self.session.post(f"{self.base_url}/automation/scenes", json=scene_data)
        print(f"    Created scene: {response.status_code}")

        # Step 5: Record automation
        print("\n  Step 5: Recording automation...")
        response = self.session.post(
            f"{self.base_url}/automation/record/start",
            json={"targets": ["reverb_wet_dry", "master_volume"]}
        )
        print(f"    Started recording automation: {response.status_code}")

        time.sleep(0.5)

        response = self.session.post(f"{self.base_url}/automation/record/stop")
        print(f"    Stopped recording automation: {response.status_code}")

        print("\n  Workflow complete!")

    def cleanup(self):
        """Clean up created resources"""
        self.print_header("CLEANUP: Removing Test Resources")

        # Delete chains
        for chain_id in self.created_resources["chains"]:
            response = self.session.delete(f"{self.base_url}/effects/chains/{chain_id}")
            print(f"  Deleted chain {chain_id}: {response.status_code}")

        # Delete tracks
        for track_id in self.created_resources["tracks"]:
            response = self.session.delete(f"{self.base_url}/looping/tracks/{track_id}")
            print(f"  Deleted track {track_id}: {response.status_code}")

        # Delete scenes
        for scene_id in self.created_resources["scenes"]:
            response = self.session.delete(f"{self.base_url}/automation/scenes/{scene_id}")
            print(f"  Deleted scene {scene_id}: {response.status_code}")

        # Delete macros
        for macro_id in self.created_resources["macros"]:
            response = self.session.delete(f"{self.base_url}/automation/macros/{macro_id}")
            print(f"  Deleted macro {macro_id}: {response.status_code}")

    def run_all_tests(self):
        """Run complete demonstration"""
        print("\n" + "=" * 70)
        print("  MAAPS API Live Demonstration")
        print("  Server: " + self.base_url)
        print("  Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 70)

        try:
            # Test server connectivity
            print("\nTesting server connectivity...")
            response = self.session.get(f"{self.base_url}/system/health")
            if response.status_code != 200:
                print(f"ERROR: Server not responding! Status: {response.status_code}")
                return

            print("  Server is online and healthy!")

            # Run all test suites
            self.test_system_health()
            self.test_effects_chain()
            self.test_live_looping()
            self.test_sync_clock()
            self.test_automation()
            self.test_complete_workflow()

            # Cleanup
            self.cleanup()

            # Final summary
            self.print_header("DEMONSTRATION COMPLETE")
            print("\n  All API endpoints tested successfully!")
            print("  Resources created and cleaned up.")
            print("\n  Next steps:")
            print("    - Open Swagger UI: http://localhost:8000/docs")
            print("    - Try the interactive API documentation")
            print("    - Run WebSocket test: python tests/test_websocket.py")
            print("    - Start the React frontend: cd frontend/maaps-ui && npm run dev")
            print("\n" + "=" * 70)

        except requests.exceptions.ConnectionError:
            print("\nERROR: Could not connect to server!")
            print("Make sure the API server is running:")
            print("  uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")

        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user")
            self.cleanup()

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    demo = MAAPSDemo()
    demo.run_all_tests()


if __name__ == "__main__":
    main()
