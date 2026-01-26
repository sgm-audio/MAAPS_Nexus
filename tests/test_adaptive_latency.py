"""
Tests for Adaptive Latency Protection Feature
"""

import unittest
import ray
import time
import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.live.performance_monitoring_agent import PerformanceMonitoringAgent, PerformanceAlert, PerformanceMetrics
from src.core import Message, Topics, Priority

class TestAdaptiveLatency(unittest.TestCase):
    """Test suite for Adaptive Latency Protection"""

    @classmethod
    def setUpClass(cls):
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)

    @classmethod
    def tearDownClass(cls):
        ray.shutdown()

    def setUp(self):
        self.agent = PerformanceMonitoringAgent()
        # Mock the publish method to intercept messages
        self.agent.publish = MagicMock()
        
        # Manually add an alert
        alert = PerformanceAlert(
            alert_id="latency_test",
            metric="audio_latency_ms",
            threshold=15.0, # 15ms threshold
            comparison="greater_than",
            callback_topic="test.callback"
        )
        self.agent.alerts[alert.alert_id] = alert

    def test_latency_throttling_trigger(self):
        """Test that high latency triggers a system.throttle message"""
        # Create a metrics object with high latency
        high_latency_metrics = PerformanceMetrics(
            cpu_usage_percent=50.0,
            memory_usage_percent=50.0,
            disk_usage_percent=50.0,
            network_latency_ms=0.0,
            audio_latency_ms=20.0, # 20ms > 15ms threshold
            buffer_load_percent=50.0,
            timestamp=time.time()
        )
        
        # Trigger check
        self.agent._check_performance_alerts(high_latency_metrics)
        
        # Verify publish calls
        # Expected calls: 
        # 1. alert callback
        # 2. monitor.alert.critical
        # 3. system.throttle
        
        calls = self.agent.publish.call_args_list
        throttle_call = None
        for call in calls:
            args, _ = call
            if args[0] == "system.throttle":
                throttle_call = call
                break
        
        self.assertIsNotNone(throttle_call, "system.throttle should have been published")
        
        # Verify payload
        args, kwargs = throttle_call
        payload = args[1]
        self.assertIn("throttle_factor", payload)
        self.assertEqual(payload['throttle_factor'], 0.5) # As defined in logic
        self.assertIn("duration", payload)

    def test_cpu_throttling_trigger(self):
        """Test that high CPU triggers a system.throttle message"""
        # Add CPU alert
        cpu_alert = PerformanceAlert(
            alert_id="cpu_test",
            metric="cpu_usage_percent",
            threshold=80.0,
            comparison="greater_than",
            callback_topic="test.callback"
        )
        self.agent.alerts[cpu_alert.alert_id] = cpu_alert
        
        # Metrics with high CPU
        high_cpu_metrics = PerformanceMetrics(
            cpu_usage_percent=90.0, # > 80.0
            memory_usage_percent=50.0,
            disk_usage_percent=50.0,
            network_latency_ms=0.0,
            audio_latency_ms=5.0,
            buffer_load_percent=50.0,
            timestamp=time.time()
        )
        
        self.agent._check_performance_alerts(high_cpu_metrics)
        
        # Verify throttle call
        calls = self.agent.publish.call_args_list
        throttle_call = None
        for call in calls:
            args, _ = call
            if args[0] == "system.throttle":
                throttle_call = call
                # Check specific payload for CPU
                if "High cpu_usage_percent" in args[1]['reason']:
                    break
        
        self.assertIsNotNone(throttle_call)
        self.assertEqual(throttle_call[0][1]['throttle_factor'], 0.25)

if __name__ == '__main__':
    unittest.main()
