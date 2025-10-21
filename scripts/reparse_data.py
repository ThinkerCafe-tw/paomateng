#!/usr/bin/env python3
"""
Re-parse existing HTML data with updated parser

This script re-extracts structured data from existing content_html
without re-scraping the website.

Usage:
    python scripts/reparse_data.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.json_storage import JSONStorage
from src.parsers.content_parser import ContentParser
from loguru import logger


def reparse_all_data():
    """Re-parse all existing announcements with updated parser"""

    print("=" * 80)
    print("Re-parsing existing data with updated parser")
    print("=" * 80)

    # Initialize components
    storage = JSONStorage()
    parser = ContentParser()

    # Load existing data
    print("\nLoading existing data...")
    announcements = storage.load()
    print(f"✓ Loaded {len(announcements)} announcements")

    if not announcements:
        print("No data to re-parse")
        return

    # Re-parse each announcement
    total_versions = 0
    updated_versions = 0

    for idx, ann in enumerate(announcements, 1):
        print(f"\nProcessing {idx}/{len(announcements)}: {ann.id}")
        print(f"  Title: {ann.title[:50]}...")
        print(f"  Publish date: {ann.publish_date}")

        for v_idx, version in enumerate(ann.version_history, 1):
            total_versions += 1

            # Re-parse with publish_date and title
            old_data = version.extracted_data
            new_data = parser.parse(version.content_html, ann.publish_date, ann.title)

            # Update version
            version.extracted_data = new_data
            updated_versions += 1

            # Show changes
            if old_data and old_data.predicted_resumption_time != new_data.predicted_resumption_time:
                print(f"  Version {v_idx}: Updated predicted_resumption_time")
                print(f"    Old: {old_data.predicted_resumption_time}")
                print(f"    New: {new_data.predicted_resumption_time}")

    # Save updated data
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  Total announcements: {len(announcements)}")
    print(f"  Total versions: {total_versions}")
    print(f"  Updated versions: {updated_versions}")
    print("=" * 80)

    print("\nSaving updated data...")
    storage.save(announcements)
    print("✓ Re-parsing complete!")


if __name__ == "__main__":
    try:
        reparse_all_data()
    except Exception as e:
        logger.error(f"Re-parsing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
