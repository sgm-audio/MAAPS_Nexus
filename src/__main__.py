"""
Main entry point for running MAAPS as a module.

Usage:
    python -m src.system
    python -m src.system --config /path/to/config.json
    python -m src.system --help
"""

import argparse
import logging
import sys
from pathlib import Path

from .system import create_system


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="MAAPS - Multi-Agent Audio Processing System"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to configuration file (default: config.json)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode (background)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)

    # Verify config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {args.config}")
        sys.exit(1)

    logger.info("Starting MAAPS Multi-Agent System...")
    logger.info(f"Using configuration: {args.config}")

    try:
        # Create and start the system
        system = create_system()
        system.start()

        logger.info("MAAPS system started successfully")
        logger.info("Press Ctrl+C to stop the system")

        if not args.daemon:
            # Keep running until interrupted
            import time

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutdown signal received...")
                system.stop()
                logger.info("MAAPS system stopped")

    except Exception as e:
        logger.error(f"Failed to start MAAPS system: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
