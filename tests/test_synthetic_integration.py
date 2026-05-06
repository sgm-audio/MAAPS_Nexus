"""
Integration Tests using Synthetic Data for MAAPS

This suite uses the SyntheticDataGenerator to stress-test agents with
diverse, randomized inputs to ensure robustness and schema compliance.
"""

import unittest
import ray
import numpy as np
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils.synthetic_data import SyntheticDataGenerator, GenerationParams
from src.agents.critic_agent import CriticAgent
from src.agents.hgo_coordinator import HGOCoordinator, AgentProposal
from src.core.audio_ontology import AudioAttribute, AgentAction


class TestSyntheticIntegration(unittest.TestCase):
    """Stress tests using synthetic data."""

    @classmethod
    def setUpClass(cls):
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)

    @classmethod
    def tearDownClass(cls):
        ray.shutdown()

    def setUp(self):
        self.generator = SyntheticDataGenerator(GenerationParams(seed=42))
        self.critic = CriticAgent.remote()
        self.coordinator = HGOCoordinator.remote()

    def test_critic_with_varied_audio(self):
        """Test Critic Agent with various synthetic audio signals."""
        signal_types = ["sine", "noise", "chirp", "complex", "silence"]

        for sig_type in signal_types:
            # Generate synthetic data
            audio = self.generator.generate_audio_samples(signal_type=sig_type)
            state = self.generator.generate_audio_state(completeness=0.5)
            goal = self.generator.generate_audio_goal()

            # Validation
            self.assertTrue(len(audio) > 0)
            self.assertTrue(self.generator.validate_audio_state(state))

            # Execute Agent Action
            evaluation = ray.get(self.critic.evaluate.remote(audio, state, [goal]))

            # Verify Output
            self.assertIsNotNone(evaluation)
            self.assertTrue(0.0 <= evaluation.satisfaction_score <= 1.0)
            self.assertIsInstance(evaluation.feedback, str)
            # print(f"Tested {sig_type}: Score {evaluation.satisfaction_score:.2f}")

    def test_coordinator_with_random_proposals(self):
        """Test HGO Coordinator with randomized agent proposals."""
        current_state = self.generator.generate_audio_state()

        proposals = []
        for i in range(5):
            # Create synthetic proposal
            action_params = {f"p{j}": np.random.random() for j in range(3)}
            action = AgentAction(
                agent_id=f"agent_{i}",
                action_type="synthetic_action",
                parameters=action_params,
            )

            # Random impact prediction
            impact = {
                attr: np.random.uniform(-0.5, 0.5)
                for attr in np.random.choice(list(AudioAttribute), 3)
            }

            prop = AgentProposal(
                agent_id=f"agent_{i}",
                action=action,
                predicted_impact=impact,
                predicted_satisfaction=np.random.random(),
                confidence=np.random.random(),
            )
            proposals.append(prop)

        # Execute Coordinator
        decision = ray.get(self.coordinator.coordinate.remote(proposals, current_state))

        # Verify
        self.assertIsNotNone(decision)
        total_processed = len(decision.approved_proposals) + len(
            decision.rejected_proposals
        )
        self.assertEqual(total_processed, 5)
        self.assertTrue(
            len(decision.execution_order) == len(decision.approved_proposals)
        )

    def test_generator_validation(self):
        """Self-test the generator validation logic."""
        buffer = self.generator.generate_audio_buffer()
        self.assertTrue(self.generator.validate_audio_buffer(buffer))

        # Corrupt buffer
        buffer.samples = []  # Invalid
        self.assertFalse(self.generator.validate_audio_buffer(buffer))


if __name__ == "__main__":
    unittest.main()
