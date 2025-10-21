#!/usr/bin/env python3
"""
Re-classify existing announcements with updated classifier

Usage:
    python scripts/reclassify_data.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.json_storage import JSONStorage
from src.classifiers.announcement_classifier import AnnouncementClassifier


def reclassify_all_data():
    """Re-classify all existing announcements"""

    print("=" * 80)
    print("Re-classifying existing data")
    print("=" * 80)

    storage = JSONStorage()
    classifier = AnnouncementClassifier()

    print("\nLoading data...")
    announcements = storage.load()
    print(f"✓ Loaded {len(announcements)} announcements\n")

    updated = 0
    for idx, ann in enumerate(announcements, 1):
        old_cat = ann.classification.category

        # Re-classify using title and first version content
        content = ann.version_history[0].content_html
        new_classification = classifier.classify(ann.title, content)

        # Update event_group_id
        new_classification.event_group_id = classifier.extract_event_group_id(
            ann.title, ann.publish_date
        )

        ann.classification = new_classification

        if old_cat != new_classification.category:
            print(f"{idx}. {ann.id}: {old_cat} → {new_classification.category}")
            print(f"   Title: {ann.title[:50]}")
            updated += 1

    print(f"\n✓ Updated {updated} classifications")

    print("\nSaving...")
    storage.save(announcements)
    print("✓ Done!")


if __name__ == "__main__":
    reclassify_all_data()
