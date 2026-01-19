"""
MAAPS Nexus - Multi-Agent Audio Processing System
Main Integration and Orchestration

This is the main entry point that brings together:
1. Ray Cluster
2. Audio Ontology
3. Critic Agent
4. EQ RL Agent
5. Dynamics RL Agent
6. HGO Coordinator
7. VST3 Integration

Run this to start the complete system.
"""

import ray
import numpy as np
import logging
import time
import argparse
from typing import Dict, List, Optional
import sys
import asyncio

# Import MAAPS components
from src.infrastructure.ray_cluster import RayClusterManager, get_or_create_cluster
from src.core.audio_ontology import (
    AudioState,
    AudioAttribute,
    AudioOntologyManager,
    create_clarity_goal,
    create_warmth_goal,
    create_reduce_mud_goal,
    create_punch_goal,
    create_balanced_mix_goals
)
from src.agents.critic_agent import CriticAgent, CriticEvaluation
from src.agents.eq_rl_agent import EQRLAgent
from src.agents.dynamics_rl_agent import DynamicsRLAgent
from src.agents.hgo_coordinator import HGOCoordinator, AgentProposal
from src.daw_integration.vst3_wrapper import VST3Communicator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MAAPSNexusSystem:
    """
    Main MAAPS Nexus system orchestrator.
    Coordinates all components and manages the audio processing pipeline.
    """

    def __init__(
        self,
        num_cpus: Optional[int] = None,
        num_gpus: Optional[int] = None,
        buffer_size: int = 512,
        sample_rate: int = 44100,
        enable_vst3: bool = True,
        use_pretrained: bool = False,
        model_dir: str = "./models"
    ):
        """
        Initialize MAAPS Nexus system.

        Args:
            num_cpus: Number of CPUs for Ray cluster
            num_gpus: Number of GPUs
            buffer_size: Audio buffer size
            sample_rate: Sample rate
            enable_vst3: Enable VST3 integration
            use_pretrained: Load pre-trained models
            model_dir: Directory for model checkpoints
        """
        self.buffer_size = buffer_size
        self.sample_rate = sample_rate
        self.enable_vst3 = enable_vst3
        self.use_pretrained = use_pretrained
        self.model_dir = model_dir

        # Initialize Ray cluster
        logger.info("Initializing Ray cluster...")
        self.cluster = RayClusterManager(num_cpus=num_cpus, num_gpus=num_gpus)
        self.cluster.initialize()

        # Initialize ontology
        logger.info("Initializing audio ontology...")
        self.ontology = AudioOntologyManager()

        # Define goals
        self.goals = create_balanced_mix_goals()

        # Initialize agents
        logger.info("Initializing agents...")
        self.critic_agent = None
        self.eq_agent = None
        self.dynamics_agent = None
        self.coordinator = None
        self._initialize_agents()

        # Initialize VST3 communicator
        self.vst3_comm = None
        if self.enable_vst3:
            logger.info("Initializing VST3 communicator...")
            self._initialize_vst3()

        # Stats
        self.total_frames_processed = 0
        self.total_training_steps = 0

        logger.info("MAAPS Nexus system initialized successfully!")

    def _initialize_agents(self):
        """Initialize all Ray agents."""
        # Critic agent
        critic_model_path = f"{self.model_dir}/critic.pth" if self.use_pretrained else None
        self.critic_agent = CriticAgent.remote(
            model_path=critic_model_path,
            ontology=self.ontology
        )

        # EQ agent
        eq_model_path = f"{self.model_dir}/eq_rl.pth" if self.use_pretrained else None
        self.eq_agent = EQRLAgent.remote(
            num_bands=8,
            sample_rate=self.sample_rate
        )
        if eq_model_path:
            ray.get(self.eq_agent.load_model.remote(eq_model_path))

        # Dynamics agent
        dynamics_model_path = f"{self.model_dir}/dynamics_rl.pth" if self.use_pretrained else None
        self.dynamics_agent = DynamicsRLAgent.remote(
            sample_rate=self.sample_rate
        )
        if dynamics_model_path:
            ray.get(self.dynamics_agent.load_model.remote(dynamics_model_path))

        # HGO Coordinator
        self.coordinator = HGOCoordinator.remote(
            goal_hierarchy=self.goals,
            ontology=self.ontology
        )

        # Register agents with coordinator
        ray.get(self.coordinator.register_agent.remote("eq_agent", self.eq_agent, priority=0.8))
        ray.get(self.coordinator.register_agent.remote("dynamics_agent", self.dynamics_agent, priority=0.7))

        logger.info("All agents initialized")

    def _initialize_vst3(self):
        """Initialize VST3 communication."""
        self.vst3_comm = VST3Communicator(
            buffer_size=self.buffer_size,
            num_channels=2,
            sample_rate=self.sample_rate
        )
        self.vst3_comm.start()
        logger.info("VST3 communication started")

    def process_audio_frame(
        self,
        audio: np.ndarray,
        current_state: AudioState
    ) -> tuple[np.ndarray, AudioState]:
        """
        Process one audio frame through the multi-agent system.

        Args:
            audio: Input audio (num_samples, num_channels)
            current_state: Current ontology state

        Returns:
            processed_audio: Output audio
            new_state: Updated state
        """
        # Convert stereo to mono for analysis (average channels)
        if audio.shape[1] == 2:
            audio_mono = np.mean(audio, axis=1)
        else:
            audio_mono = audio[:, 0]

        # Step 1: Get proposals from agents
        eq_processed_ref = self.eq_agent.process_audio.remote(audio_mono, current_state)
        dynamics_processed_ref = self.dynamics_agent.process_audio.remote(audio_mono, current_state)

        # Wait for agent processing
        eq_processed, eq_action = ray.get(eq_processed_ref)
        dynamics_processed, dynamics_action = ray.get(dynamics_processed_ref)

        # Create proposals
        eq_proposal = AgentProposal(
            agent_id="eq_agent",
            action=eq_action,
            predicted_impact={AudioAttribute.CLARITY: 0.1},  # Simplified
            predicted_satisfaction=0.7,
            confidence=0.8
        )

        dynamics_proposal = AgentProposal(
            agent_id="dynamics_agent",
            action=dynamics_action,
            predicted_impact={AudioAttribute.PUNCH: 0.1},  # Simplified
            predicted_satisfaction=0.75,
            confidence=0.85
        )

        # Step 2: Coordinate between agents
        decision = ray.get(
            self.coordinator.coordinate.remote(
                [eq_proposal, dynamics_proposal],
                current_state
            )
        )

        # Step 3: Execute approved actions
        processed_audio = audio_mono.copy()

        for proposal in decision.approved_proposals:
            if proposal.agent_id == "eq_agent":
                processed_audio = eq_processed
            elif proposal.agent_id == "dynamics_agent":
                processed_audio = dynamics_processed

        # Step 4: Evaluate result with Critic
        new_state = AudioState()
        # Simple state update (in real system, would extract features)
        for attr in AudioAttribute:
            new_state.set_attribute(attr, np.random.rand() * 0.5 + 0.5)  # Placeholder

        evaluation: CriticEvaluation = ray.get(
            self.critic_agent.evaluate.remote(
                processed_audio,
                new_state,
                self.goals,
                self.sample_rate
            )
        )

        # Step 5: Update agents with reward (RL training)
        reward = evaluation.reward

        # Store experiences for training
        ray.get([
            self.eq_agent.store_experience.remote(
                current_state,
                np.zeros(24),  # Placeholder action vector
                reward,
                new_state,
                False
            ),
            self.dynamics_agent.store_experience.remote(
                current_state,
                np.zeros(7),  # Placeholder action vector
                reward,
                new_state,
                False
            )
        ])

        # Periodic training
        if self.total_frames_processed % 100 == 0:
            ray.get([
                self.eq_agent.train_step.remote(batch_size=32),
                self.dynamics_agent.train_step.remote(batch_size=32)
            ])
            self.total_training_steps += 1

        # Convert mono back to stereo
        if audio.shape[1] == 2:
            processed_audio_stereo = np.stack([processed_audio, processed_audio], axis=1)
        else:
            processed_audio_stereo = processed_audio.reshape(-1, 1)

        self.total_frames_processed += 1

        return processed_audio_stereo, new_state

    def run_vst3_processing_loop(self):
        """Main processing loop for VST3 integration."""
        logger.info("Starting VST3 processing loop...")

        current_state = AudioState()
        # Initialize state
        for attr in AudioAttribute:
            current_state.set_attribute(attr, 0.5)

        try:
            while True:
                # Get audio from VST3
                audio = self.vst3_comm.get_audio_for_processing(timeout=0.1)

                if audio is not None:
                    # Process
                    processed, new_state = self.process_audio_frame(audio, current_state)

                    # Send back to VST3
                    self.vst3_comm.send_processed_audio(processed)

                    current_state = new_state

                    # Log stats periodically
                    if self.total_frames_processed % 1000 == 0:
                        latency_info = self.vst3_comm.get_latency_info()
                        logger.info(
                            f"Processed {self.total_frames_processed} frames, "
                            f"latency: {latency_info['latency_ms']:.2f}ms, "
                            f"training steps: {self.total_training_steps}"
                        )

                        # Get coordinator stats
                        stats = ray.get(self.coordinator.get_statistics.remote())
                        logger.info(f"Coordinator stats: {stats}")

                time.sleep(0.0001)  # Small sleep to prevent CPU spinning

        except KeyboardInterrupt:
            logger.info("Stopping processing loop...")
        finally:
            self.shutdown()

    def run_standalone_test(self, duration_seconds: float = 10.0):
        """Run standalone test without VST3."""
        logger.info(f"Running standalone test for {duration_seconds} seconds...")

        current_state = AudioState()
        for attr in AudioAttribute:
            current_state.set_attribute(attr, 0.5)

        num_frames = int(duration_seconds * self.sample_rate / self.buffer_size)

        for i in range(num_frames):
            # Generate test audio (white noise)
            audio = np.random.randn(self.buffer_size, 2) * 0.1

            # Process
            processed, new_state = self.process_audio_frame(audio, current_state)
            current_state = new_state

            if i % 10 == 0:
                logger.info(f"Frame {i}/{num_frames}, satisfaction: {current_state.get_attribute(AudioAttribute.CLARITY):.2f}")

        logger.info("Test complete!")
        self.print_statistics()

    def print_statistics(self):
        """Print system statistics."""
        logger.info("=== MAAPS Nexus Statistics ===")
        logger.info(f"Total frames processed: {self.total_frames_processed}")
        logger.info(f"Total training steps: {self.total_training_steps}")

        # Get agent stats
        stats = ray.get(self.coordinator.get_statistics.remote())
        logger.info(f"Coordinator stats: {stats}")

        # Get cluster info
        cluster_info = self.cluster.get_cluster_info()
        logger.info(f"Cluster resources: {cluster_info['available_resources']}")

    def save_models(self, output_dir: str = "./models"):
        """Save all trained models."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"Saving models to {output_dir}...")
        ray.get([
            self.critic_agent.save_model.remote(f"{output_dir}/critic.pth"),
            self.eq_agent.save_model.remote(f"{output_dir}/eq_rl.pth"),
            self.dynamics_agent.save_model.remote(f"{output_dir}/dynamics_rl.pth")
        ])
        logger.info("Models saved successfully")

    def shutdown(self):
        """Shutdown the system gracefully."""
        logger.info("Shutting down MAAPS Nexus system...")

        if self.vst3_comm:
            self.vst3_comm.close()

        self.cluster.shutdown()
        logger.info("Shutdown complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MAAPS Nexus - Multi-Agent Audio Processing System")
    parser.add_argument("--mode", choices=["vst3", "test"], default="vst3",
                        help="Run mode: vst3 (DAW integration) or test (standalone)")
    parser.add_argument("--buffer-size", type=int, default=512,
                        help="Audio buffer size")
    parser.add_argument("--sample-rate", type=int, default=44100,
                        help="Sample rate")
    parser.add_argument("--num-cpus", type=int, default=None,
                        help="Number of CPUs for Ray cluster")
    parser.add_argument("--test-duration", type=float, default=10.0,
                        help="Test duration in seconds (test mode only)")
    parser.add_argument("--model-dir", type=str, default="./models",
                        help="Directory for model checkpoints")
    parser.add_argument("--use-pretrained", action="store_true",
                        help="Load pre-trained models")

    args = parser.parse_args()

    # Initialize system
    system = MAAPSNexusSystem(
        num_cpus=args.num_cpus,
        buffer_size=args.buffer_size,
        sample_rate=args.sample_rate,
        enable_vst3=(args.mode == "vst3"),
        use_pretrained=args.use_pretrained,
        model_dir=args.model_dir
    )

    # Run based on mode
    if args.mode == "vst3":
        system.run_vst3_processing_loop()
    else:
        system.run_standalone_test(duration_seconds=args.test_duration)
        system.save_models(args.model_dir)


if __name__ == "__main__":
    main()
