"""
Comprehensive API Integration Tests
Tests all Phase 2 & 3 endpoints with the running server
"""

import os
import pytest
import requests
import json
from typing import Dict, Any

# API Base URL
BASE_URL = os.getenv("MAAPS_BASE_URL", "http://127.0.0.1:18000")
API_V1 = f"{BASE_URL}/api/v1"


@pytest.fixture(scope="module")
def created_chain():
    payload = {
        "chain_name": "Fixture Vocal Chain",
        "effects": [
            {
                "type": "compressor",
                "parameters": {"threshold": -18.0, "ratio": 4.0},
                "bypass": False,
                "wet_dry": 1.0,
            }
        ],
    }
    resp = requests.post(f"{API_V1}/effects/chains", json=payload)
    assert resp.status_code == 201
    return resp.json()["data"]


@pytest.fixture(scope="module")
def chain_id(created_chain):
    return created_chain["chain_id"]


@pytest.fixture(scope="module")
def effect_id(created_chain):
    effects = created_chain.get("effects", [])
    if effects:
        return effects[0]["effect_id"]
    chain_resp = requests.get(
        f"{API_V1}/effects/chains/{created_chain['chain_id']}"
    ).json()
    return chain_resp["data"]["effects"][0]["effect_id"]


@pytest.fixture(scope="module")
def track_id():
    payload = {
        "track_name": "Fixture Drums",
        "length_beats": 4,
        "sync_to_tempo": True,
        "volume": 0.8,
        "pan": 0.0,
    }
    resp = requests.post(f"{API_V1}/looping/tracks", json=payload)
    assert resp.status_code == 201
    return resp.json()["data"]["track_id"]


@pytest.fixture(scope="module")
def macro_id():
    payload = {
        "macro_name": "Fixture Energy",
        "target_parameters": [
            {
                "param": "effects.eq.gain3",
                "min": 0.0,
                "max": 6.0,
                "curve": "exponential",
            }
        ],
    }
    resp = requests.post(f"{API_V1}/automation/macros", json=payload)
    assert resp.status_code == 201
    return resp.json()["data"]["macro_id"]


@pytest.fixture(scope="module")
def token():
    resp = requests.post(
        f"{API_V1}/auth/login",
        json={"username": "admin", "password": "password"},
    )
    assert resp.status_code == 200
    return resp.json()["token"]


class TestEffectsChainAPI:
    """Test Effects Chain endpoints"""

    def test_create_effect_chain(self):
        """Test creating an effect chain"""
        payload = {
            "chain_name": "Test Vocal Chain",
            "effects": [
                {
                    "type": "gate",
                    "parameters": {"threshold": -40.0, "attack": 5.0, "release": 50.0},
                    "bypass": False,
                    "wet_dry": 1.0,
                },
                {
                    "type": "compressor",
                    "parameters": {
                        "threshold": -18.0,
                        "ratio": 4.0,
                        "attack": 5.0,
                        "release": 50.0,
                    },
                    "bypass": False,
                    "wet_dry": 1.0,
                },
            ],
        }

        response = requests.post(f"{API_V1}/effects/chains", json=payload)
        print(f"\n[OK] Create Chain Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert "chain_id" in data["data"]

        return data["data"]["chain_id"]

    def test_list_effect_chains(self):
        """Test listing all effect chains"""
        response = requests.get(f"{API_V1}/effects/chains")
        print(f"\n[OK] List Chains Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_update_effect_parameters(self, chain_id: str, effect_id: str):
        """Test updating effect parameters"""
        payload = {"parameters": {"threshold": -20.0, "ratio": 6.0}}

        url = f"{API_V1}/effects/chains/{chain_id}/effects/{effect_id}/parameters"
        response = requests.patch(url, json=payload)
        print(
            f"\n[OK] Update Parameters Response: {json.dumps(response.json(), indent=2)}"
        )

        assert response.status_code == 200


class TestLiveLoopingAPI:
    """Test Live Looping endpoints"""

    def test_create_loop_track(self):
        """Test creating a loop track"""
        payload = {
            "track_name": "Test Drums",
            "length_beats": 4,
            "sync_to_tempo": True,
            "volume": 0.8,
            "pan": 0.0,
        }

        response = requests.post(f"{API_V1}/looping/tracks", json=payload)
        print(f"\n[OK] Create Track Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert "track_id" in data["data"]

        return data["data"]["track_id"]

    def test_list_loop_tracks(self):
        """Test listing all loop tracks"""
        response = requests.get(f"{API_V1}/looping/tracks")
        print(f"\n[OK] List Tracks Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_start_recording(self, track_id: str):
        """Test starting loop recording"""
        payload = {"mode": "replace"}

        response = requests.post(
            f"{API_V1}/looping/tracks/{track_id}/record/start", json=payload
        )
        print(
            f"\n[OK] Start Recording Response: {json.dumps(response.json(), indent=2)}"
        )

        assert response.status_code == 200

    def test_stop_recording(self, track_id: str):
        """Test stopping loop recording"""
        response = requests.post(f"{API_V1}/looping/tracks/{track_id}/record/stop")
        print(
            f"\n[OK] Stop Recording Response: {json.dumps(response.json(), indent=2)}"
        )

        assert response.status_code == 200


class TestSyncClockAPI:
    """Test Sync & Clock endpoints"""

    def test_set_tempo(self):
        """Test setting tempo"""
        payload = {"bpm": 128.0, "time_signature": "4/4"}

        response = requests.post(f"{API_V1}/sync/tempo/set", json=payload)
        print(f"\n[OK] Set Tempo Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_tap_tempo(self):
        """Test tap tempo"""
        response = requests.post(f"{API_V1}/sync/tempo/tap")
        print(f"\n[OK] Tap Tempo Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200

    def test_transport_play(self):
        """Test transport play"""
        response = requests.post(f"{API_V1}/sync/transport/play")
        print(
            f"\n[OK] Transport Play Response: {json.dumps(response.json(), indent=2)}"
        )

        assert response.status_code == 200

    def test_transport_stop(self):
        """Test transport stop"""
        response = requests.post(f"{API_V1}/sync/transport/stop")
        print(
            f"\n[OK] Transport Stop Response: {json.dumps(response.json(), indent=2)}"
        )

        assert response.status_code == 200

    def test_get_clock_status(self):
        """Test getting clock status"""
        response = requests.get(f"{API_V1}/sync/status")
        print(f"\n[OK] Clock Status Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200


class TestAutomationAPI:
    """Test Performance Automation endpoints"""

    def test_create_scene(self):
        """Test creating automation scene"""
        payload = {
            "scene_name": "Test Drop",
            "parameter_snapshots": {
                "effects.filter.cutoff": 20000.0,
                "effects.reverb.wet_dry": 0.4,
                "effects.delay.feedback": 0.6,
            },
            "transition_time": 2.0,
        }

        response = requests.post(f"{API_V1}/automation/scenes", json=payload)
        print(f"\n[OK] Create Scene Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"

        return data["data"]["scene_id"]

    def test_create_macro(self):
        """Test creating macro control"""
        payload = {
            "macro_name": "Test Energy",
            "target_parameters": [
                {
                    "param": "effects.eq.gain3",
                    "min": 0.0,
                    "max": 6.0,
                    "curve": "exponential",
                },
                {
                    "param": "effects.compressor.ratio",
                    "min": 2.0,
                    "max": 8.0,
                    "curve": "logarithmic",
                },
            ],
        }

        response = requests.post(f"{API_V1}/automation/macros", json=payload)
        print(f"\n[OK] Create Macro Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"

        return data["data"]["macro_id"]

    def test_change_macro_value(self, macro_id: str):
        """Test changing macro value"""
        payload = {"value": 0.75}

        response = requests.post(
            f"{API_V1}/automation/macros/{macro_id}/value", json=payload
        )
        print(f"\n[OK] Change Macro Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200

    def test_create_cue(self):
        """Test creating performance cue"""
        payload = {
            "cue_name": "Test Drop at 2:30",
            "timecode": "00:02:30.000",
            "actions": [
                {
                    "action_type": "scene_change",
                    "parameters": {"scene_id": "scene_drop"},
                },
                {
                    "action_type": "parameter_change",
                    "parameters": {
                        "parameter_path": "effects.filter.cutoff",
                        "value": 5000.0,
                    },
                },
            ],
        }

        response = requests.post(f"{API_V1}/automation/cues", json=payload)
        print(f"\n[OK] Create Cue Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 201


class TestSystemAPI:
    """Test System endpoints"""

    def test_get_health(self):
        """Test system health endpoint"""
        response = requests.get(f"{API_V1}/system/health")
        print(f"\n[OK] System Health Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_metrics(self):
        """Test system metrics endpoint"""
        response = requests.get(f"{API_V1}/system/metrics")
        print(
            f"\n[OK] System Metrics Response: {json.dumps(response.json(), indent=2)}"
        )

        assert response.status_code == 200

    def test_list_agents(self):
        """Test list agents endpoint"""
        response = requests.get(f"{API_V1}/system/agents")
        print(f"\n[OK] List Agents Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200


class TestAuthentication:
    """Test Authentication endpoints"""

    def test_login(self):
        """Test login endpoint"""
        payload = {"username": "admin", "password": "password"}

        response = requests.post(f"{API_V1}/auth/login", json=payload)
        print(f"\n[OK] Login Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200
        data = response.json()
        assert "token" in data

        return data["token"]

    def test_verify_token(self, token: str):
        """Test token verification"""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_V1}/auth/verify", headers=headers)
        print(f"\n[OK] Verify Token Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200


def run_all_tests():
    """Run all API tests"""
    print("\n" + "=" * 80)
    print("MAAPS API Integration Tests")
    print("=" * 80)

    # Test Effects Chain
    print("\n" + "-" * 80)
    print("Testing Effects Chain API")
    print("-" * 80)
    effects_tests = TestEffectsChainAPI()
    chain_id = effects_tests.test_create_effect_chain()
    effects_tests.test_list_effect_chains()

    # Test Live Looping
    print("\n" + "-" * 80)
    print("Testing Live Looping API")
    print("-" * 80)
    looping_tests = TestLiveLoopingAPI()
    track_id = looping_tests.test_create_loop_track()
    looping_tests.test_list_loop_tracks()
    looping_tests.test_start_recording(track_id)
    looping_tests.test_stop_recording(track_id)

    # Test Sync & Clock
    print("\n" + "-" * 80)
    print("Testing Sync & Clock API")
    print("-" * 80)
    sync_tests = TestSyncClockAPI()
    sync_tests.test_set_tempo()
    sync_tests.test_tap_tempo()
    sync_tests.test_transport_play()
    sync_tests.test_get_clock_status()
    sync_tests.test_transport_stop()

    # Test Automation
    print("\n" + "-" * 80)
    print("Testing Performance Automation API")
    print("-" * 80)
    automation_tests = TestAutomationAPI()
    scene_id = automation_tests.test_create_scene()
    macro_id = automation_tests.test_create_macro()
    automation_tests.test_change_macro_value(macro_id)
    automation_tests.test_create_cue()

    # Test System
    print("\n" + "-" * 80)
    print("Testing System API")
    print("-" * 80)
    system_tests = TestSystemAPI()
    system_tests.test_get_health()
    system_tests.test_get_metrics()
    system_tests.test_list_agents()

    # Test Authentication
    print("\n" + "-" * 80)
    print("Testing Authentication API")
    print("-" * 80)
    auth_tests = TestAuthentication()
    token = auth_tests.test_login()
    auth_tests.test_verify_token(token)

    print("\n" + "=" * 80)
    print("All API Tests Completed Successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_all_tests()
