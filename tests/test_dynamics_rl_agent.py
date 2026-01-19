"""
Tests for Dynamics RL Agent
"""

import unittest
import ray
import sys
import os
import numpy as np
import torch

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.dynamics_rl_agent import DynamicsRLAgent
from src.core.audio_ontology import AudioState, AgentAction, AudioAttribute

class TestDynamicsRLAgent(unittest.TestCase):
    """Test suite for Dynamics RL Agent"""

    def setUp(self):
        """Set up agent for each test"""
        self.agent = DynamicsRLAgent.remote()
        
        # Create dummy audio
        sr = 44100
        t = np.linspace(0, 0.1, int(sr * 0.1)) # 100ms
        self.dummy_audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        self.current_state = AudioState()

    def test_process_audio(self):
        """Test audio processing"""
        processed, action = ray.get(self.agent.process_audio.remote(
            self.dummy_audio,
            self.current_state
        ))
        
        # Check audio
        self.assertEqual(len(processed), len(self.dummy_audio))
        self.assertIsInstance(processed, np.ndarray)
        
        # Check action
        self.assertIsInstance(action, AgentAction)
        self.assertEqual(action.agent_id, "dynamics_rl_agent")
        self.assertEqual(action.action_type, "dynamics_adjustment")
        self.assertTrue(len(action.parameters) > 0)
        self.assertIn("threshold", action.parameters)

    def test_training_pipeline(self):
        """Test store experience and train step"""
        next_state = AudioState()
        next_state.set_attribute(AudioAttribute.PUNCH, 0.6)
        
        # Action dim = 7
        action_vector = np.zeros(7)
        
        # Add samples
        for _ in range(10):
            ray.get(self.agent.store_experience.remote(
                self.current_state,
                action_vector,
                np.random.rand(),
                next_state,
                False
            ))
            
        metrics = ray.get(self.agent.train_step.remote(batch_size=5))
        
        self.assertIsNotNone(metrics)
        self.assertIn("critic_loss", metrics)

if __name__ == '__main__':
    unittest.main()
