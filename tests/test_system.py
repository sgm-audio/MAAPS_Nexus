"""
Test Suite for Multi-Agent Audio Processing System

Basic tests to verify system functionality.
"""

import sys
import os
import time
import unittest
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.system import create_system


class TestSystemBasics(unittest.TestCase):
    """Test basic system operations"""

    @classmethod
    def setUpClass(cls):
        """Set up test system once for all tests"""
        cls.system = create_system()
        cls.system.start()
        time.sleep(2)  # Allow system to initialize

    @classmethod
    def tearDownClass(cls):
        """Tear down test system"""
        cls.system.stop()

    def test_01_system_startup(self):
        """Test system can start and is healthy"""
        health = self.system.get_health()

        self.assertIsNotNone(health)
        self.assertIn('health_score', health)
        self.assertGreater(health['health_score'], 50, "System health should be > 50%")
        self.assertGreater(health['agents_healthy'], 0, "Should have healthy agents")

    def test_02_all_agents_running(self):
        """Test all agents are running"""
        agents = self.system.get_all_agents()

        self.assertGreater(len(agents), 0, "Should have agents registered")

        # Check each agent is running
        for agent in agents:
            self.assertEqual(
                agent['state'], 'running',
                f"Agent {agent['agent_name']} should be running"
            )

    def test_03_audio_enhancement_basic(self):
        """Test basic audio enhancement"""
        # Create test audio
        sample_rate = 44100
        duration = 0.5
        num_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, num_samples)
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Test enhancement
        result = self.system.enhance_audio(
            audio_data=audio_data.tolist(),
            sample_rate=sample_rate
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.get('success'), f"Enhancement should succeed: {result.get('error')}")
        self.assertIn('enhanced_audio', result)

    def test_04_music_generation_melody(self):
        """Test melody generation"""
        musical_context = {
            'key': 'C major',
            'tempo': 120.0,
            'time_signature': '4/4',
            'length_bars': 4
        }

        result = self.system.generate_music(
            content_type='melody',
            musical_context=musical_context
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.get('success'), f"Melody generation should succeed: {result.get('error')}")
        self.assertIn('melody_notes', result)
        self.assertGreater(len(result['melody_notes']), 0, "Should generate notes")

    def test_05_metadata_extraction(self):
        """Test metadata extraction"""
        # Create test audio
        sample_rate = 44100
        duration = 1.0
        num_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, num_samples)
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        result = self.system.extract_metadata(
            audio_data=audio_data.tolist(),
            sample_rate=sample_rate,
            deep_analysis=True
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.get('success'), f"Metadata extraction should succeed: {result.get('error')}")
        self.assertIn('metadata', result)

        metadata = result['metadata']
        self.assertEqual(metadata['sample_rate'], sample_rate)
        self.assertAlmostEqual(metadata['duration'], duration, delta=0.1)

    def test_06_resource_metrics(self):
        """Test resource monitoring"""
        result = self.system.get_resource_metrics()

        self.assertIsNotNone(result)
        self.assertTrue(result.get('success'), "Resource metrics should be available")
        self.assertIn('metrics', result)

        metrics = result['metrics']
        self.assertIn('cpu_usage_percent', metrics)
        self.assertIn('memory_usage_percent', metrics)

    def test_07_workflow_creation(self):
        """Test workflow creation"""
        workflow_def = {
            'name': 'Test Workflow',
            'description': 'A test workflow',
            'steps': [
                {
                    'step_id': 'test_step',
                    'name': 'Test Step',
                    'agent_id': 'test_agent',
                    'topic': 'test.topic',
                    'payload': {},
                    'dependencies': []
                }
            ]
        }

        workflow_id = self.system.create_workflow(workflow_def)

        self.assertIsNotNone(workflow_id)
        self.assertIsInstance(workflow_id, str)
        self.assertGreater(len(workflow_id), 0)

    def test_08_message_bus_metrics(self):
        """Test message bus is working"""
        health = self.system.get_health()
        bus_metrics = health.get('message_bus_metrics', {})

        self.assertGreater(
            bus_metrics.get('messages_delivered', 0),
            0,
            "Message bus should have delivered messages"
        )


class TestAgentInteraction(unittest.TestCase):
    """Test agent interactions"""

    @classmethod
    def setUpClass(cls):
        """Set up test system"""
        cls.system = create_system()
        cls.system.start()
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        """Tear down test system"""
        cls.system.stop()

    def test_enhancement_to_metadata_flow(self):
        """Test data flow from enhancement to metadata"""
        # Create test audio
        sample_rate = 44100
        duration = 0.5
        num_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, num_samples)
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Enhance audio
        enhancement_result = self.system.enhance_audio(
            audio_data=audio_data.tolist(),
            sample_rate=sample_rate
        )

        self.assertTrue(enhancement_result.get('success'))

        # Extract metadata from enhanced audio
        enhanced_audio = enhancement_result.get('enhanced_audio')
        metadata_result = self.system.extract_metadata(
            audio_data=enhanced_audio,
            sample_rate=sample_rate
        )

        self.assertTrue(metadata_result.get('success'))
        self.assertIn('metadata', metadata_result)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSystemBasics))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentInteraction))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
