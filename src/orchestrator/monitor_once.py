#!/usr/bin/env python3
"""
Single-cycle monitor for GitHub Actions

This script runs ONE monitoring cycle and exits, designed for scheduled execution
via GitHub Actions cron jobs.

Usage:
    python -m src.orchestrator.monitor_once
"""

import sys
import yaml
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator.monitor import run_monitoring_cycle
from src.utils.logger import setup_logging


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    """Execute single monitoring cycle"""
    # Load configuration
    config = load_config("config/settings.yaml")

    # Setup logging
    setup_logging(config)

    # Run one cycle
    print("=" * 80)
    print("GitHub Actions: Single Monitoring Cycle")
    print("=" * 80)

    try:
        run_monitoring_cycle(config)
        print("\n✓ Monitoring cycle completed successfully")
        sys.exit(0)

    except Exception as e:
        print(f"\n✗ Monitoring cycle failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
