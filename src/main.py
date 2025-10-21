"""
Main entry point for Railway News Monitor
"""

import argparse
import sys
import yaml
from pathlib import Path
from loguru import logger

from src.utils.logger import setup_logging
from src.orchestrator.historical_scraper import run_historical_scrape
from src.orchestrator.monitor import start_monitoring


def load_config(config_path: str) -> dict:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load configuration from {config_path}: {e}")
        sys.exit(1)


def main():
    """
    Main CLI entry point
    """
    parser = argparse.ArgumentParser(
        description="Railway News Monitor - TRA Announcement Tracking System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run historical scrape
  python -m src.main --mode historical

  # Run monitoring mode (default 5 minutes interval)
  python -m src.main --mode monitor

  # Run monitoring with custom interval
  python -m src.main --mode monitor --interval 10

  # Use custom config file
  python -m src.main --mode historical --config my_config.yaml
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["historical", "monitor"],
        required=True,
        help="Operation mode: 'historical' for full scrape, 'monitor' for continuous monitoring",
    )

    parser.add_argument(
        "--interval",
        type=int,
        help="Monitoring interval in minutes (only for monitor mode)",
    )

    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="Path to configuration file (default: config/settings.yaml)",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Setup logging
    setup_logging(config)

    logger.info("=" * 80)
    logger.info("Railway News Monitor")
    logger.info("=" * 80)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Config: {args.config}")

    try:
        if args.mode == "historical":
            # Run historical scrape
            run_historical_scrape(config)

        elif args.mode == "monitor":
            # Override interval if provided
            if args.interval:
                config["monitoring"]["interval_minutes"] = args.interval
                logger.info(f"Monitoring interval override: {args.interval} minutes")

            # Start monitoring
            start_monitoring(config)

    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
