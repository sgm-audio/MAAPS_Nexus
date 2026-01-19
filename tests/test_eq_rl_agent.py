"""
Tests for EQ RL Agent
"""

import unittest
import ray
import sys
import os
import numpy as np
import torch

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.eq_rl_agent import EQRLAgent
from src.core.audio_ontology import AudioState, AgentAction, AudioAttribute

class TestEQRLAgent(unittest.TestCase):
    """Test suite for EQ RL Agent"""

    def setUp(self):
        """Set up agent for each test"""
        self.agent = EQRLAgent.remote(num_bands=4) # Smaller num bands for faster test
        
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
        self.assertEqual(action.agent_id, "eq_rl_agent")
        self.assertEqual(action.action_type, "eq_adjustment")
        self.assertTrue(len(action.parameters) > 0)

    def test_training_pipeline(self):
        """Test store experience and train step"""
        # Store some dummy experience
        next_state = AudioState()
        next_state.set_attribute(AudioAttribute.CLARITY, 0.6)
        
        # We need to simulate an action vector. 
        # Num bands = 4. Action dim = 4 * 3 = 12.
        action_vector = np.zeros(12)
        
        ray.get(self.agent.store_experience.remote(
            self.current_state,
            action_vector,
            0.5, # reward
            next_state,
            False # done
        ))
        
        # Train
        # Batch size 1 to ensure we can train with just 1 sample (though usually batch size is larger)
        # But replay buffer might need more samples before sampling?
        # ReplayBuffer.sample calls np.random.choice with replace=False.
        # So we need at least batch_size samples.
        
        # Add more samples
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
