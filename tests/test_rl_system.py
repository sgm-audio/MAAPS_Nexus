"""
Tests for the MAAPS Nexus RL System (src.nexus_system)
"""

import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nexus_system import MAAPSNexusSystem
from src.core.audio_ontology import AudioState, AudioAttribute
from src.agents.hgo_coordinator import AgentProposal, CoordinationDecision


class TestRLSystem(unittest.TestCase):
    """Test suite for the main RL system orchestrator."""

    def setUp(self):
        """Set up system for each test."""
        # Mock Ray
        self.ray_patcher = patch("src.nexus_system.ray")
        self.mock_ray = self.ray_patcher.start()

        # Mock ray.get to return values immediately
        def side_effect(ref):
            if isinstance(ref, list):
                return [r.value if hasattr(r, "value") else r for r in ref]
            return ref.value if hasattr(ref, "value") else ref

        self.mock_ray.get.side_effect = side_effect

        # Mock agents
        self.mock_critic = MagicMock()
        self.mock_eq = MagicMock()
        self.mock_dynamics = MagicMock()
        self.mock_coordinator = MagicMock()

        # Mock remote calls returning objects with .value attribute for side_effect
        # Or simpler: just return the mock result directly, but ray.get expects something.
        # Let's make the side_effect return the argument itself if it's not a list
        self.mock_ray.get.side_effect = lambda x: x if not isinstance(x, list) else x

        # Mock agent initialization in system
        with (
            patch(
                "src.agents.critic_agent.CriticAgent.remote",
                return_value=self.mock_critic,
            ),
            patch("src.agents.eq_rl_agent.EQRLAgent.remote", return_value=self.mock_eq),
            patch(
                "src.agents.dynamics_rl_agent.DynamicsRLAgent.remote",
                return_value=self.mock_dynamics,
            ),
            patch(
                "src.agents.hgo_coordinator.HGOCoordinator.remote",
                return_value=self.mock_coordinator,
            ),
        ):
            self.system = MAAPSNexusSystem(
                num_cpus=2,
                buffer_size=512,
                sample_rate=44100,
                plugin_mode="none",
                use_pretrained=False,
                model_dir="./test_models",
            )

    def tearDown(self):
        """Clean up."""
        self.ray_patcher.stop()

    def test_initialization(self):
        """Test that the system initializes all components."""
        self.assertIsNotNone(self.system.cluster)
        self.assertIsNotNone(self.system.ontology)
        self.assertIsNotNone(self.system.critic_agent)
        self.assertIsNotNone(self.system.eq_agent)
        self.assertIsNotNone(self.system.dynamics_agent)
        self.assertIsNotNone(self.system.coordinator)

    def test_process_audio_frame(self):
        """Test processing a single audio frame."""
        # Create dummy audio (mono)
        buffer_size = 512
        audio = np.random.randn(buffer_size) * 0.1

        current_state = AudioState()
        for attr in AudioAttribute:
            current_state.set_attribute(attr, 0.5)

        # Mock agent responses
        # EQ Agent
        eq_processed = np.zeros(buffer_size)
        eq_action = MagicMock()
        self.mock_eq.process_audio.remote.return_value = (eq_processed, eq_action)

        # Dynamics Agent
        dyn_processed = np.zeros(buffer_size)
        dyn_action = MagicMock()
        self.mock_dynamics.process_audio.remote.return_value = (
            dyn_processed,
            dyn_action,
        )

        # Coordinator
        decision = CoordinationDecision(
            approved_proposals=[
                AgentProposal(
                    agent_id="eq_agent",
                    action=eq_action,
                    predicted_impact={},
                    predicted_satisfaction=0.8,
                    confidence=1.0,
                )
            ],
            rejected_proposals=[],
            execution_order=["eq_agent"],
            compromise_adjustments={},
            reasoning="Test",
        )
        self.mock_coordinator.coordinate.remote.return_value = decision

        # Critic
        evaluation = MagicMock()
        evaluation.reward = 0.5
        self.mock_critic.evaluate.remote.return_value = evaluation

        # Process frame
        processed_audio, new_state = self.system.process_audio_frame(
            audio, current_state
        )

        # Check output structure
        self.assertIsInstance(processed_audio, np.ndarray)
        self.assertIsInstance(new_state, AudioState)

        # Verify interactions
        self.mock_eq.process_audio.remote.assert_called()
        self.mock_dynamics.process_audio.remote.assert_called()
        self.mock_coordinator.coordinate.remote.assert_called()
        self.mock_critic.evaluate.remote.assert_called()

    def test_standalone_test_run(self):
        """Test the standalone test runner."""
        # Mock process_audio_frame to avoid setting up all inner mocks again
        with patch.object(self.system, "process_audio_frame") as mock_process:
            mock_process.return_value = (np.zeros((512, 1)), AudioState())

            # Run for a very short duration
            self.system.run_standalone_test(duration_seconds=0.1)

            self.assertGreater(mock_process.call_count, 0)


if __name__ == "__main__":
    unittest.main()
