#!/usr/bin/env python3
"""
MAAPS Nexus - Multi-Agent Audio Processing System
Main Integration Script

This script:
1. Initializes Ray cluster for distributed execution
2. Sets up all agents (Critic, EQ, Dynamics, HGO Coordinator)
3. Launches VST3 backend for DAW integration
4. Provides training and inference modes
"""

import argparse
import logging
import signal
import sys
import time
from typing import Optional

from src.infrastructure.ray_cluster import (
    RayClusterConfig,
    initialize_ray_cluster,
    RayClusterManager,
    DistributedAgentPool
)
from src.core.message_bus import MessageBus
from src.core.audio_ontology import get_audio_ontology
from src.agents.critic_agent import CriticAgent
from src.agents.eq_rl_agent import EQRLAgent
from src.agents.dynamics_rl_agent import DynamicsRLAgent
from src.agents.hgo_coordinator import HGOCoordinator, OptimizationGoal, GoalPriority
from src.daw_integration.vst3_wrapper import (
    VST3Backend,
    SharedMemoryConfig,
    create_vst3_backend_for_hgo
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MAAPSNexusSystem:
    """
    Main MAAPS Nexus system orchestrator.

    Manages all components and provides unified interface.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

        # Core components
        self.ray_cluster: Optional[RayClusterManager] = None
        self.message_bus: Optional[MessageBus] = None
        self.agent_pool: Optional[DistributedAgentPool] = None

        # Agents
        self.critic_agent: Optional[CriticAgent] = None
        self.eq_agent: Optional[EQRLAgent] = None
        self.dynamics_agent: Optional[DynamicsRLAgent] = None
        self.hgo_coordinator: Optional[HGOCoordinator] = None

        # VST3 Backend
        self.vst3_backend: Optional[VST3Backend] = None

        # System state
        self.initialized = False
        self.running = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def initialize(self):
        """Initialize all system components"""
        try:
            logger.info("="*60)
            logger.info("MAAPS NEXUS - Multi-Agent Audio Processing System")
            logger.info("="*60)

            # Step 1: Initialize Ray cluster
            logger.info("Step 1/7: Initializing Ray cluster...")
            ray_config = RayClusterConfig(
                num_cpus=self.config.get('num_cpus'),
                num_gpus=self.config.get('num_gpus', 0),
                include_dashboard=True,
                namespace="maaps_nexus",
            )
            self.ray_cluster = initialize_ray_cluster(ray_config)
            logger.info(f"✓ Ray cluster initialized: {self.ray_cluster.get_cluster_status()}")

            # Step 2: Initialize audio ontology
            logger.info("Step 2/7: Loading audio ontology...")
            ontology = get_audio_ontology()
            logger.info(f"✓ Ontology loaded with {len(ontology.concepts)} concepts")

            # Step 3: Initialize message bus
            logger.info("Step 3/7: Initializing message bus...")
            self.message_bus = MessageBus()
            self.message_bus.start()
            logger.info("✓ Message bus started")

            # Step 4: Initialize agents
            logger.info("Step 4/7: Initializing agents...")

            # Critic Agent
            self.critic_agent = CriticAgent(
                agent_id="critic_agent_main",
                message_bus=self.message_bus,
                config=self.config.get('critic', {})
            )
            self.critic_agent.start()
            logger.info("  ✓ Critic agent started")

            # EQ RL Agent
            self.eq_agent = EQRLAgent(
                agent_id="eq_rl_agent_main",
                message_bus=self.message_bus,
                critic_agent_id=self.critic_agent.agent_id,
                config=self.config.get('eq', {})
            )
            self.eq_agent.start()
            logger.info("  ✓ EQ RL agent started")

            # Dynamics RL Agent
            self.dynamics_agent = DynamicsRLAgent(
                agent_id="dynamics_rl_agent_main",
                message_bus=self.message_bus,
                critic_agent_id=self.critic_agent.agent_id,
                config=self.config.get('dynamics', {})
            )
            self.dynamics_agent.start()
            logger.info("  ✓ Dynamics RL agent started")

            # HGO Coordinator
            self.hgo_coordinator = HGOCoordinator(
                agent_id="hgo_coordinator_main",
                message_bus=self.message_bus,
                eq_agent_id=self.eq_agent.agent_id,
                dynamics_agent_id=self.dynamics_agent.agent_id,
                critic_agent_id=self.critic_agent.agent_id,
                config=self.config.get('hgo', {})
            )
            self.hgo_coordinator.start()
            logger.info("  ✓ HGO Coordinator started")

            # Set default optimization goals
            self._set_default_goals()

            # Step 5: Create distributed agent pool (optional)
            if self.config.get('use_distributed_agents', False):
                logger.info("Step 5/7: Creating distributed agent pool...")
                self.agent_pool = DistributedAgentPool(self.ray_cluster)
                # Add agent pools as needed
                logger.info("✓ Distributed agent pool created")
            else:
                logger.info("Step 5/7: Skipping distributed agent pool (not enabled)")

            # Step 6: Initialize VST3 backend
            if self.config.get('enable_vst3', True):
                logger.info("Step 6/7: Initializing VST3 backend...")
                self.vst3_backend = create_vst3_backend_for_hgo(
                    self.hgo_coordinator.agent_id,
                    self.message_bus
                )
                self.vst3_backend.start()
                logger.info("✓ VST3 backend started")
                logger.info(f"  Shared memory: {self.vst3_backend.config.shm_name}")
                logger.info(f"  Control socket: {self.vst3_backend.config.socket_path}")
            else:
                logger.info("Step 6/7: Skipping VST3 backend (not enabled)")

            # Step 7: System ready
            logger.info("Step 7/7: System initialization complete")
            self.initialized = True
            self.running = True

            logger.info("="*60)
            logger.info("MAAPS NEXUS IS READY")
            logger.info("="*60)
            logger.info("")
            logger.info("System Status:")
            logger.info(f"  Ray Dashboard: http://127.0.0.1:8265")
            logger.info(f"  Agents Running: 4 (Critic, EQ, Dynamics, HGO)")
            logger.info(f"  VST3 Backend: {'Active' if self.vst3_backend else 'Disabled'}")
            logger.info("")
            logger.info("Ready to process audio!")
            logger.info("")

        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            self.shutdown()
            raise

    def _set_default_goals(self):
        """Set default optimization goals"""
        goals = [
            OptimizationGoal(
                name="clarity_and_presence",
                description="Maximize clarity and presence",
                target_concepts=["clarity", "presence", "brightness"],
                avoid_concepts=["mud", "dullness"],
                priority=GoalPriority.HIGH,
                weight=1.0,
            ),
            OptimizationGoal(
                name="controlled_dynamics",
                description="Control dynamics while preserving punch",
                target_concepts=["punch", "tightness", "controlled"],
                avoid_concepts=["squashed", "flat"],
                priority=GoalPriority.MEDIUM,
                weight=0.8,
            ),
        ]

        self.hgo_coordinator.set_goals(goals)
        logger.info(f"  ✓ Set {len(goals)} default optimization goals")

    def train_mode(self, audio_file: str, episodes: int = 10):
        """
        Run training mode on audio file.

        Args:
            audio_file: Path to audio file
            episodes: Number of training episodes
        """
        import librosa
        import numpy as np

        if not self.initialized:
            raise RuntimeError("System not initialized")

        logger.info(f"Starting training mode: {episodes} episodes")

        # Load audio
        audio, sr = librosa.load(audio_file, sr=44100, mono=False)
        if audio.ndim == 1:
            audio = np.stack([audio, audio])  # Stereo

        logger.info(f"Loaded audio: {audio.shape}, sr={sr}")

        # Run training episodes
        for episode in range(episodes):
            logger.info(f"\n--- Episode {episode + 1}/{episodes} ---")

            # Coordinate agents in training mode
            result = self.hgo_coordinator.coordinate_agents(
                audio[0],  # Use first channel
                training=True,
                max_steps=5
            )

            logger.info(f"Episode {episode + 1} results:")
            logger.info(f"  Initial reward: {result['initial_reward']:.3f}")
            logger.info(f"  Final reward: {result['final_reward']:.3f}")
            logger.info(f"  Improvement: {result['improvement']:.3f}")
            logger.info(f"  Cooperation score: {result['cooperation_score']:.3f}")
            logger.info(f"  Conflicts: {result['conflicts_detected']}")

        logger.info("\nTraining complete!")

    def inference_mode(self, audio_file: str, output_file: str):
        """
        Run inference mode on audio file.

        Args:
            audio_file: Path to input audio
            output_file: Path to output audio
        """
        import librosa
        import soundfile as sf
        import numpy as np

        if not self.initialized:
            raise RuntimeError("System not initialized")

        logger.info(f"Processing audio: {audio_file}")

        # Load audio
        audio, sr = librosa.load(audio_file, sr=44100, mono=False)
        if audio.ndim == 1:
            audio = np.stack([audio, audio])

        logger.info(f"Loaded audio: {audio.shape}, sr={sr}")

        # Process through HGO coordinator
        result = self.hgo_coordinator.coordinate_agents(
            audio[0],
            training=False,
            max_steps=1  # Single pass for inference
        )

        processed_audio = result['processed_audio']

        # Save output
        sf.write(output_file, processed_audio, sr)

        logger.info(f"Processed audio saved to: {output_file}")
        logger.info(f"  Initial quality: {result['initial_reward']:.3f}")
        logger.info(f"  Final quality: {result['final_reward']:.3f}")
        logger.info(f"  Improvement: {result['improvement']:.3f}")

    def run_forever(self):
        """Run system forever (for VST3 mode)"""
        if not self.initialized:
            raise RuntimeError("System not initialized")

        logger.info("Running in daemon mode (press Ctrl+C to stop)...")

        try:
            while self.running:
                time.sleep(1.0)

                # Print statistics every 10 seconds
                if int(time.time()) % 10 == 0:
                    if self.vst3_backend:
                        logger.info(
                            f"VST3 Stats: {self.vst3_backend.blocks_processed} blocks, "
                            f"avg latency: {self.vst3_backend.total_latency / max(1, self.vst3_backend.blocks_processed):.2f}ms"
                        )

        except KeyboardInterrupt:
            logger.info("Shutting down...")

    def shutdown(self):
        """Shutdown all system components"""
        logger.info("Shutting down MAAPS Nexus system...")

        self.running = False

        # Stop VST3 backend
        if self.vst3_backend:
            self.vst3_backend.stop()
            logger.info("✓ VST3 backend stopped")

        # Stop agents
        if self.hgo_coordinator:
            self.hgo_coordinator.stop()
        if self.dynamics_agent:
            self.dynamics_agent.stop()
        if self.eq_agent:
            self.eq_agent.stop()
        if self.critic_agent:
            self.critic_agent.stop()
        logger.info("✓ Agents stopped")

        # Stop message bus
        if self.message_bus:
            self.message_bus.stop()
            logger.info("✓ Message bus stopped")

        # Shutdown Ray cluster
        if self.ray_cluster:
            self.ray_cluster.shutdown_cluster()
            logger.info("✓ Ray cluster shutdown")

        logger.info("System shutdown complete")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MAAPS Nexus Multi-Agent Audio Processing System")

    parser.add_argument(
        "--mode",
        choices=["vst3", "train", "inference"],
        default="vst3",
        help="Operating mode (default: vst3)"
    )

    parser.add_argument(
        "--audio-file",
        type=str,
        help="Audio file for training or inference"
    )

    parser.add_argument(
        "--output-file",
        type=str,
        help="Output file for inference mode"
    )

    parser.add_argument(
        "--episodes",
        type=int,
        default=10,
        help="Number of training episodes (default: 10)"
    )

    parser.add_argument(
        "--num-cpus",
        type=int,
        help="Number of CPUs for Ray cluster (auto-detect if not specified)"
    )

    parser.add_argument(
        "--num-gpus",
        type=int,
        default=0,
        help="Number of GPUs for Ray cluster (default: 0)"
    )

    parser.add_argument(
        "--no-vst3",
        action="store_true",
        help="Disable VST3 backend"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.mode in ["train", "inference"] and not args.audio_file:
        parser.error(f"{args.mode} mode requires --audio-file")

    if args.mode == "inference" and not args.output_file:
        parser.error("inference mode requires --output-file")

    # Create system configuration
    config = {
        'num_cpus': args.num_cpus,
        'num_gpus': args.num_gpus,
        'enable_vst3': not args.no_vst3 and args.mode == "vst3",
    }

    # Initialize system
    system = MAAPSNexusSystem(config)
    system.initialize()

    try:
        # Run in specified mode
        if args.mode == "vst3":
            system.run_forever()

        elif args.mode == "train":
            system.train_mode(args.audio_file, args.episodes)

        elif args.mode == "inference":
            system.inference_mode(args.audio_file, args.output_file)

    finally:
        system.shutdown()


if __name__ == "__main__":
    main()
