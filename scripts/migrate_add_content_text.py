#!/usr/bin/env python3
"""
Migration script to add content_text field to existing announcements

This script:
1. Loads existing master.json
2. For each version_entry in each announcement:
   - Converts content_html to content_text using html_to_text()
   - Adds the content_text field
3. Saves the updated data back to master.json (with backup)

Usage:
    python scripts/migrate_add_content_text.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.json_storage import JSONStorage
from src.utils.text_utils import html_to_text
from loguru import logger


def migrate_add_content_text():
    """Add content_text field to all existing announcements"""

    logger.info("=" * 80)
    logger.info("Migration: Adding content_text to existing data")
    logger.info("=" * 80)

    # Initialize storage
    storage = JSONStorage(
        output_file="data/master.json",
        backup_dir="data/backups",
        pretty_print=True,
    )

    # Load existing data
    logger.info("Loading existing data...")
    announcements = storage.load()
    logger.info(f"Loaded {len(announcements)} announcements")

    if not announcements:
        logger.warning("No announcements found. Nothing to migrate.")
        return

    # Process each announcement
    total_versions = 0
    updated_versions = 0

    for idx, announcement in enumerate(announcements, 1):
        logger.info(f"Processing announcement {idx}/{len(announcements)}: {announcement.id}")

        for version in announcement.version_history:
            total_versions += 1

            # Check if content_text already exists
            if hasattr(version, 'content_text') and version.content_text:
                logger.debug(f"  Version {version.scraped_at} already has content_text, skipping")
                continue

            # Convert HTML to text
            try:
                content_text = html_to_text(version.content_html)
                version.content_text = content_text
                updated_versions += 1
                logger.debug(f"  Added content_text ({len(content_text)} chars) to version {version.scraped_at}")
            except Exception as e:
                logger.error(f"  Failed to convert HTML to text: {e}")
                # Set empty string as fallback
                version.content_text = ""

    # Save updated data
    logger.info("=" * 80)
    logger.info(f"Migration Summary:")
    logger.info(f"  Total announcements: {len(announcements)}")
    logger.info(f"  Total versions: {total_versions}")
    logger.info(f"  Updated versions: {updated_versions}")
    logger.info("=" * 80)

    if updated_versions > 0:
        logger.info("Saving updated data...")
        storage.save(announcements)
        logger.info("✓ Migration complete! Data saved to data/master.json")
        logger.info("  Backup created in data/backups/")
    else:
        logger.info("No updates needed. All versions already have content_text.")


if __name__ == "__main__":
    try:
        migrate_add_content_text()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
