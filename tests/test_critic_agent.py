"""
Tests for Critic Agent
"""

import unittest
import ray
import sys
import os
import numpy as np
import torch

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.critic_agent import CriticAgent, CriticEvaluation
from src.core.audio_ontology import AudioState, AudioAttribute, create_clarity_goal


class TestCriticAgent(unittest.TestCase):
    """Test suite for Critic Agent"""

    def setUp(self):
        """Set up critic for each test"""
        self.critic = CriticAgent.remote()

        # Create dummy audio (1 second sine wave)
        sr = 44100
        t = np.linspace(0, 1, sr)
        self.dummy_audio = 0.5 * np.sin(2 * np.pi * 440 * t)

        self.current_state = AudioState()
        self.goals = [create_clarity_goal()]

    def test_initialization(self):
        """Test critic initialization"""
        # We can't easily check internal state of remote actor without exposing methods
        # But if we can call methods, it's initialized
        self.assertIsNotNone(self.critic)

    def test_feature_extraction(self):
        """Test feature extraction (exposed via a wrapper or by checking evaluate)"""
        # We can't call extract_audio_features directly on the actor as it's not exposed as remote method
        # Wait, usually only public methods are remote-able.
        # But `extract_audio_features` is a method of the class.
        # Ray exposes all public methods.

        features = ray.get(self.critic.extract_audio_features.remote(self.dummy_audio))
        self.assertEqual(len(features), 128)
        self.assertIsInstance(features, np.ndarray)

    def test_evaluate(self):
        """Test evaluation"""
        evaluation = ray.get(
            self.critic.evaluate.remote(
                self.dummy_audio, self.current_state, self.goals
            )
        )

        self.assertIsInstance(evaluation, CriticEvaluation)
        self.assertGreaterEqual(evaluation.satisfaction_score, 0.0)
        self.assertLessEqual(evaluation.satisfaction_score, 1.0)
        self.assertIsInstance(evaluation.attribute_scores, dict)
        self.assertTrue(len(evaluation.feedback) > 0)

    def test_training_step(self):
        """Test training step"""
        # Create a small batch
        batch_size = 2
        audio_batch = [self.dummy_audio] * batch_size
        state_batch = [self.current_state] * batch_size
        labels = [0.8] * batch_size

        loss = ray.get(self.critic.train_step.remote(audio_batch, state_batch, labels))

        self.assertIsInstance(loss, float)
        self.assertGreaterEqual(loss, 0.0)

        # Check stats
        stats = ray.get(self.critic.get_training_stats.remote())
        self.assertEqual(stats["total_steps"], 1)


if __name__ == "__main__":
    unittest.main()
