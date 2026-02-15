"""
MAAPS Nexus - Multi-Agent Audio Processing System
Core System Implementation

This module contains the main system orchestrator that manages:
1. Ray Cluster lifecycle
2. Audio Ontology
3. Agent initialization and coordination
4. Audio processing pipeline
5. Plugin integration (VST3, CLAP, ARA)
"""

import ray
import numpy as np
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import os

# Import MAAPS components
from src.infrastructure.ray_cluster import RayClusterManager
from src.core.audio_ontology import (
    AudioState,
    AudioAttribute,
    AudioOntologyManager,
    create_balanced_mix_goals,
)
from src.agents.critic_agent import CriticAgent, CriticEvaluation
from src.agents.eq_rl_agent import EQRLAgent
from src.agents.dynamics_rl_agent import DynamicsRLAgent
from src.agents.hgo_coordinator import HGOCoordinator, AgentProposal

# Import Plugin Wrappers
try:
    from src.daw_integration.streaming_plugin_wrapper import StreamingPluginCommunicator
except ImportError:
    StreamingPluginCommunicator = None  # type: ignore

try:
    from src.daw_integration.ara_plugin_wrapper import AraPluginCommunicator
except ImportError:
    AraPluginCommunicator = None  # type: ignore

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
        plugin_mode: str = "vst3",  # "vst3", "clap", "ara", "none"
        use_pretrained: bool = False,
        model_dir: str = "./models",
    ):
        """
        Initialize MAAPS Nexus system.

        Args:
            num_cpus: Number of CPUs for Ray cluster
            num_gpus: Number of GPUs
            buffer_size: Audio buffer size
            sample_rate: Sample rate
            plugin_mode: "vst3", "clap", "ara", or "none" (standalone test)
            use_pretrained: Load pre-trained models
            model_dir: Directory for model checkpoints
        """
        self.buffer_size = buffer_size
        self.sample_rate = sample_rate
        self.plugin_mode = plugin_mode
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
        self.critic_agent: Optional[Any] = None
        self.eq_agent: Optional[Any] = None
        self.dynamics_agent: Optional[Any] = None
        self.coordinator: Optional[Any] = None
        self._initialize_agents()

        # Initialize Plugin communicator
        self.streaming_comm: Optional[Any] = None
        self.ara_comm: Optional[Any] = None

        if self.plugin_mode != "none":
            self._initialize_plugin_comm()

        # Stats
        self.total_frames_processed = 0
        self.total_training_steps = 0

        logger.info("MAAPS Nexus system initialized successfully!")

    def _initialize_agents(self):
        """Initialize all Ray agents."""
        # Ensure model directory exists if using pretrained
        if self.use_pretrained and not os.path.exists(self.model_dir):
            logger.warning(
                f"Model directory {self.model_dir} not found. Starting with fresh models."
            )
            self.use_pretrained = False

        # Critic agent
        critic_model_path = (
            f"{self.model_dir}/critic.pth" if self.use_pretrained else None
        )
        self.critic_agent = CriticAgent.remote(
            model_path=critic_model_path, ontology=self.ontology
        )

        # EQ agent
        eq_model_path = f"{self.model_dir}/eq_rl.pth" if self.use_pretrained else None
        self.eq_agent = EQRLAgent.remote(num_bands=8, sample_rate=self.sample_rate)
        if eq_model_path and os.path.exists(eq_model_path):
            ray.get(self.eq_agent.load_model.remote(eq_model_path))

        # Dynamics agent
        dynamics_model_path = (
            f"{self.model_dir}/dynamics_rl.pth" if self.use_pretrained else None
        )
        self.dynamics_agent = DynamicsRLAgent.remote(sample_rate=self.sample_rate)
        if dynamics_model_path and os.path.exists(dynamics_model_path):
            ray.get(self.dynamics_agent.load_model.remote(dynamics_model_path))

        # HGO Coordinator
        self.coordinator = HGOCoordinator.remote(
            goal_hierarchy=self.goals, ontology=self.ontology
        )

        # Register agents with coordinator
        ray.get(
            self.coordinator.register_agent.remote(
                "eq_agent", self.eq_agent, priority=0.8
            )
        )
        ray.get(
            self.coordinator.register_agent.remote(
                "dynamics_agent", self.dynamics_agent, priority=0.7
            )
        )

        logger.info("All agents initialized")

    def _initialize_plugin_comm(self):
        """Initialize appropriate plugin communicator."""

        # Streaming (VST3/CLAP)
        if self.plugin_mode in ["vst3", "clap"]:
            if StreamingPluginCommunicator:
                self.streaming_comm = StreamingPluginCommunicator(
                    buffer_size=self.buffer_size,
                    num_channels=2,
                    sample_rate=self.sample_rate,
                    plugin_format=self.plugin_mode,
                )
                self.streaming_comm.start()
                logger.info(
                    f"{self.plugin_mode.upper()} streaming communication started"
                )
            else:
                logger.error("StreamingPluginCommunicator not available")

        # ARA
        if self.plugin_mode == "ara":
            if AraPluginCommunicator:
                self.ara_comm = AraPluginCommunicator(
                    callback_handler=self.handle_ara_request
                )
                self.ara_comm.start()
                logger.info("ARA communication started")
            else:
                logger.error("AraPluginCommunicator not available")

    def handle_ara_request(self, request: Dict) -> Dict:
        """Handle incoming ARA analysis request."""
        logger.info(f"Processing ARA Request: {request}")
        # Placeholder for real logic
        # 1. Load file
        # 2. Extract metadata
        # 3. Return analysis
        return {"status": "ok", "analysis": "placeholder_spectral_data"}

    def process_audio_frame(
        self, audio: np.ndarray, current_state: AudioState
    ) -> Tuple[np.ndarray, AudioState]:
        """
        Process one audio frame through the multi-agent system.

        Args:
            audio: Input audio (num_samples, num_channels)
            current_state: Current ontology state

        Returns:
            processed_audio: Output audio
            new_state: Updated state
        """
        if (
            self.eq_agent is None
            or self.dynamics_agent is None
            or self.coordinator is None
            or self.critic_agent is None
        ):
            raise RuntimeError("Agents not initialized")

        # Convert stereo to mono for analysis (average channels)
        if audio.ndim > 1 and audio.shape[1] == 2:
            audio_mono = np.mean(audio, axis=1)
        else:
            audio_mono = audio.flatten() if audio.ndim > 1 else audio

        # Step 1: Get proposals from agents
        eq_processed_ref = self.eq_agent.process_audio.remote(audio_mono, current_state)
        dynamics_processed_ref = self.dynamics_agent.process_audio.remote(
            audio_mono, current_state
        )

        # Wait for agent processing
        eq_processed, eq_action = ray.get(eq_processed_ref)
        dynamics_processed, dynamics_action = ray.get(dynamics_processed_ref)

        # Create proposals
        eq_proposal = AgentProposal(
            agent_id="eq_agent",
            action=eq_action,
            predicted_impact={AudioAttribute.CLARITY: 0.1},  # Simplified
            predicted_satisfaction=0.7,
            confidence=0.8,
        )

        dynamics_proposal = AgentProposal(
            agent_id="dynamics_agent",
            action=dynamics_action,
            predicted_impact={AudioAttribute.PUNCH: 0.1},  # Simplified
            predicted_satisfaction=0.75,
            confidence=0.85,
        )

        # Step 2: Coordinate between agents
        decision = ray.get(
            self.coordinator.coordinate.remote(
                [eq_proposal, dynamics_proposal], current_state
            )
        )

        # Step 3: Execute approved actions
        # TODO: This logic assumes exclusive execution. Real mixing is more complex.
        processed_audio = audio_mono.copy()

        for proposal in decision.approved_proposals:
            if proposal.agent_id == "eq_agent":
                processed_audio = eq_processed
            elif proposal.agent_id == "dynamics_agent":
                processed_audio = dynamics_processed

        # Step 4: Evaluate result with Critic
        new_state = AudioState()
        # Simple state update (in real system, would extract features)
        # TODO: Implement real feature extraction
        for attr in AudioAttribute:
            # Placeholder: Drift slightly from current state or random
            new_state.set_attribute(attr, np.random.rand() * 0.5 + 0.5)

        evaluation: CriticEvaluation = ray.get(
            self.critic_agent.evaluate.remote(
                processed_audio, new_state, self.goals, self.sample_rate
            )
        )

        # Step 5: Update agents with reward (RL training)
        reward = evaluation.reward

        # Store experiences for training
        ray.get(
            [
                self.eq_agent.store_experience.remote(
                    current_state,
                    np.zeros(24),  # Placeholder action vector
                    reward,
                    new_state,
                    False,
                ),
                self.dynamics_agent.store_experience.remote(
                    current_state,
                    np.zeros(7),  # Placeholder action vector
                    reward,
                    new_state,
                    False,
                ),
            ]
        )

        # Periodic training
        if self.total_frames_processed % 100 == 0:
            ray.get(
                [
                    self.eq_agent.train_step.remote(batch_size=32),
                    self.dynamics_agent.train_step.remote(batch_size=32),
                ]
            )
            self.total_training_steps += 1

        # Convert mono back to stereo
        if audio.ndim > 1 and audio.shape[1] == 2:
            processed_audio_stereo = np.stack(
                [processed_audio, processed_audio], axis=1
            )
        else:
            processed_audio_stereo = processed_audio.reshape(-1, 1)

        self.total_frames_processed += 1

        return processed_audio_stereo, new_state

    def run_streaming_processing_loop(self):
        """Main processing loop for VST3/CLAP integration."""
        if not self.streaming_comm:
            logger.error("Streaming communicator not initialized")
            return

        logger.info(f"Starting {self.plugin_mode.upper()} processing loop...")

        current_state = AudioState()
        # Initialize state
        for attr in AudioAttribute:
            current_state.set_attribute(attr, 0.5)

        try:
            while True:
                # Get audio from Plugin
                audio = self.streaming_comm.get_audio_for_processing(timeout=0.1)

                if audio is not None:
                    # Process
                    processed, new_state = self.process_audio_frame(
                        audio, current_state
                    )

                    # Send back to Plugin
                    self.streaming_comm.send_processed_audio(processed)

                    current_state = new_state

                    # Log stats periodically
                    if self.total_frames_processed % 1000 == 0:
                        latency_info = self.streaming_comm.get_latency_info()
                        if self.coordinator:
                            stats = ray.get(self.coordinator.get_statistics.remote())
                        else:
                            stats = {}

                        logger.info(
                            f"Processed {self.total_frames_processed} frames, "
                            f"latency: {latency_info.get('latency_ms', 0):.2f}ms, "
                            f"training steps: {self.total_training_steps}"
                        )
                        logger.info(f"Coordinator stats: {stats}")

                time.sleep(0.0001)  # Small sleep to prevent CPU spinning

        except KeyboardInterrupt:
            logger.info("Stopping processing loop...")
        finally:
            self.shutdown()

    def run_ara_loop(self):
        """Keep system alive for ARA requests."""
        logger.info("Running in ARA mode (waiting for requests)...")
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
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
                val = current_state.get_attribute(AudioAttribute.CLARITY)
                logger.info(f"Frame {i}/{num_frames}, satisfaction: {val:.2f}")

        logger.info("Test complete!")
        self.print_statistics()

    def print_statistics(self):
        """Print system statistics."""
        logger.info("=== MAAPS Nexus Statistics ===")
        logger.info(f"Total frames processed: {self.total_frames_processed}")
        logger.info(f"Total training steps: {self.total_training_steps}")

        # Get agent stats
        if self.coordinator:
            stats = ray.get(self.coordinator.get_statistics.remote())
            logger.info(f"Coordinator stats: {stats}")

        # Get cluster info
        cluster_info = self.cluster.get_cluster_info()
        logger.info(f"Cluster resources: {cluster_info.get('available_resources', {})}")

    def save_models(self, output_dir: str = "./models"):
        """Save all trained models."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        logger.info(f"Saving models to {output_dir}...")

        futures = []
        if self.critic_agent:
            futures.append(
                self.critic_agent.save_model.remote(f"{output_dir}/critic.pth")
            )
        if self.eq_agent:
            futures.append(self.eq_agent.save_model.remote(f"{output_dir}/eq_rl.pth"))
        if self.dynamics_agent:
            futures.append(
                self.dynamics_agent.save_model.remote(f"{output_dir}/dynamics_rl.pth")
            )

        if futures:
            ray.get(futures)

        logger.info("Models saved successfully")

    def shutdown(self):
        """Shutdown the system gracefully."""
        logger.info("Shutting down MAAPS Nexus system...")

        if self.streaming_comm:
            self.streaming_comm.close()

        if self.ara_comm:
            self.ara_comm.stop()

        self.cluster.shutdown()
        logger.info("Shutdown complete")
