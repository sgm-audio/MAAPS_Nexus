"""
Load Testing Suite for MAAPS API

Uses Locust for simulating concurrent users and measuring API performance.
Run with: locust -f tests/performance/load_test.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
import random
import json
import base64
import numpy as np
import time
from typing import Dict, Any


class MAAPSUser(HttpUser):
    """Simulated user interacting with MAAPS API"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Initialize user session"""
        # Generate test audio data (1 second of random audio)
        sample_rate = 44100
        duration = 1.0
        samples = int(sample_rate * duration)
        self.test_audio = np.random.randn(samples).astype(np.float32)
        self.test_audio_b64 = base64.b64encode(self.test_audio.tobytes()).decode(
            "utf-8"
        )

        # Track metrics
        self.task_count = 0
        self.errors = 0

    @task(10)
    def check_health(self):
        """Health check endpoint (most frequent)"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("health_score", 0) < 50:
                    response.failure(f"Low health score: {data['health_score']}")
                else:
                    response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(5)
    def get_metrics(self):
        """Get system metrics"""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(3)
    def enhance_audio(self):
        """Audio enhancement endpoint"""
        payload = {
            "audio_data": self.test_audio_b64,
            "sample_rate": 44100,
            "noise_reduction": random.uniform(0.5, 1.0),
            "declicking_sensitivity": random.uniform(0.3, 0.8),
            "preserve_transients": random.choice([True, False]),
        }

        with self.client.post(
            "/audio/enhance", json=payload, catch_response=True, name="/audio/enhance"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "enhanced_audio" in data:
                    response.success()
                else:
                    response.failure("Missing enhanced_audio in response")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    def generate_melody(self):
        """Music generation endpoint"""
        payload = {
            "instrument": random.choice(["piano", "synth", "guitar"]),
            "key": random.choice(["C", "G", "D", "A", "E", "F"]),
            "tempo": random.randint(80, 140),
            "duration": random.uniform(2.0, 4.0),
            "complexity": random.uniform(0.3, 0.8),
        }

        with self.client.post(
            "/music/generate", json=payload, catch_response=True, name="/music/generate"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "audio_data" in data:
                    response.success()
                else:
                    response.failure("Missing audio_data in response")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    def extract_metadata(self):
        """Metadata extraction endpoint"""
        payload = {
            "audio_data": self.test_audio_b64,
            "sample_rate": 44100,
            "include_spectral": True,
            "include_temporal": True,
            "include_harmonic": True,
        }

        with self.client.post(
            "/metadata/extract",
            json=payload,
            catch_response=True,
            name="/metadata/extract",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "metadata" in data:
                    response.success()
                else:
                    response.failure("Missing metadata in response")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def execute_workflow(self):
        """Complete workflow execution (least frequent, most expensive)"""
        payload = {
            "workflow_name": f"load_test_{random.randint(1000, 9999)}",
            "steps": [
                {
                    "agent": "audio_enhancement",
                    "operation": "enhance",
                    "params": {"noise_reduction_amount": 0.7},
                },
                {
                    "agent": "metadata_management",
                    "operation": "extract_features",
                    "params": {},
                },
            ],
            "input_data": {"audio_data": self.test_audio_b64, "sample_rate": 44100},
        }

        with self.client.post(
            "/workflow/execute",
            json=payload,
            catch_response=True,
            name="/workflow/execute",
            timeout=30,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "completed":
                    response.success()
                else:
                    response.failure(f"Workflow status: {data.get('status')}")
            else:
                response.failure(f"Status: {response.status_code}")


class HighLoadUser(HttpUser):
    """User simulating high-intensity operations"""

    wait_time = between(0.5, 1.5)

    def on_start(self):
        """Initialize with larger audio data"""
        sample_rate = 44100
        duration = 5.0  # 5 seconds
        samples = int(sample_rate * duration)
        self.test_audio = np.random.randn(samples).astype(np.float32)
        self.test_audio_b64 = base64.b64encode(self.test_audio.tobytes()).decode(
            "utf-8"
        )

    @task
    def batch_processing(self):
        """Batch processing endpoint"""
        payload = {
            "operations": [
                {"type": "enhance", "params": {"noise_reduction": 0.8}},
                {"type": "extract_metadata", "params": {"include_spectral": True}},
            ],
            "audio_files": [
                {
                    "id": f"file_{i}",
                    "audio_data": self.test_audio_b64,
                    "sample_rate": 44100,
                }
                for i in range(3)
            ],
        }

        with self.client.post(
            "/batch/process",
            json=payload,
            catch_response=True,
            name="/batch/process",
            timeout=60,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "results" in data and len(data["results"]) == 3:
                    response.success()
                else:
                    response.failure("Incomplete batch results")
            else:
                response.failure(f"Status: {response.status_code}")


# Custom event handlers for tracking metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("\n" + "=" * 60)
    print("MAAPS Load Test Started")
    print("=" * 60)
    environment.start_time = time.time()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops - print summary"""
    duration = time.time() - environment.start_time
    stats = environment.stats

    print("\n" + "=" * 60)
    print("MAAPS Load Test Summary")
    print("=" * 60)
    print(f"Duration: {duration:.2f}s")
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print(f"Avg Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print(
        """
MAAPS Load Testing Suite
========================

Run with:
  locust -f tests/performance/load_test.py --host=http://localhost:8000

Options:
  --users 100          Number of concurrent users
  --spawn-rate 10      Users spawned per second
  --run-time 5m        Test duration
  --headless           Run without web UI
  --csv=results        Save results to CSV

Example:
  locust -f tests/performance/load_test.py \\
    --host=http://localhost:8000 \\
    --users 50 \\
    --spawn-rate 5 \\
    --run-time 3m \\
    --headless \\
    --csv=results/load_test
"""
    )
