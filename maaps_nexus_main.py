"""
MAAPS Nexus - Multi-Agent Audio Processing System
Main Entry Point

This is the main entry point that brings together:
1. Ray Cluster
2. Audio Ontology
3. Critic Agent
4. EQ RL Agent
5. Dynamics RL Agent
6. HGO Coordinator
7. Plugin Integration (VST3, CLAP, ARA)

Run this to start the complete system.
"""

import argparse
from src.nexus_system import MAAPSNexusSystem


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MAAPS Nexus - Multi-Agent Audio Processing System"
    )
    parser.add_argument(
        "--mode",
        choices=["vst3", "clap", "ara", "test"],
        default="vst3",
        help="Run mode: vst3, clap, ara, or test (standalone)",
    )
    parser.add_argument(
        "--buffer-size", type=int, default=512, help="Audio buffer size"
    )
    parser.add_argument("--sample-rate", type=int, default=44100, help="Sample rate")
    parser.add_argument(
        "--num-cpus", type=int, default=None, help="Number of CPUs for Ray cluster"
    )
    parser.add_argument(
        "--test-duration",
        type=float,
        default=10.0,
        help="Test duration in seconds (test mode only)",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="./models",
        help="Directory for model checkpoints",
    )
    parser.add_argument(
        "--use-pretrained", action="store_true", help="Load pre-trained models"
    )

    args = parser.parse_args()

    # Determine plugin mode
    plugin_mode = "none"
    if args.mode in ["vst3", "clap", "ara"]:
        plugin_mode = args.mode

    # Initialize system
    system = MAAPSNexusSystem(
        num_cpus=args.num_cpus,
        buffer_size=args.buffer_size,
        sample_rate=args.sample_rate,
        plugin_mode=plugin_mode,
        use_pretrained=args.use_pretrained,
        model_dir=args.model_dir,
    )

    # Run based on mode
    if args.mode in ["vst3", "clap"]:
        system.run_streaming_processing_loop()
    elif args.mode == "ara":
        system.run_ara_loop()
    else:
        system.run_standalone_test(duration_seconds=args.test_duration)
        system.save_models(args.model_dir)


if __name__ == "__main__":
    main()
