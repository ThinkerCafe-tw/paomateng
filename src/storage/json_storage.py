"""
JSON storage manager with atomic writes and file locking
"""

import json
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from filelock import FileLock
from loguru import logger

from src.models.announcement import Announcement, VersionEntry


class JSONStorage:
    """
    Storage manager for announcement data with atomic writes
    """

    def __init__(
        self,
        output_file: str = "data/master.json",
        backup_dir: str = "data/backups",
        pretty_print: bool = True,
    ):
        """
        Initialize JSON storage manager

        Args:
            output_file: Path to main JSON file
            backup_dir: Directory for backups
            pretty_print: Whether to format JSON with indentation
        """
        self.output_file = Path(output_file)
        self.backup_dir = Path(backup_dir)
        self.pretty_print = pretty_print
        self.lock_file = Path(str(self.output_file) + ".lock")

        # Ensure directories exist
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> List[Announcement]:
        """
        Load announcements from JSON file

        Returns:
            List of Announcement objects
        """
        if not self.output_file.exists():
            logger.info(f"No existing data file found at {self.output_file}")
            return []

        try:
            with FileLock(self.lock_file, timeout=10):
                with open(self.output_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Validate and convert to Pydantic models
                announcements = [Announcement(**item) for item in data]
                logger.info(f"Loaded {len(announcements)} announcements from {self.output_file}")
                return announcements

        except Exception as e:
            logger.error(f"Failed to load data from {self.output_file}: {e}")
            return []

    def save(self, data: List[Announcement]) -> None:
        """
        Save announcements to JSON file with atomic writes

        Args:
            data: List of Announcement objects to save
        """
        try:
            # Create backup before saving
            self._create_backup()

            with FileLock(self.lock_file, timeout=10):
                # Convert Pydantic models to dict with JSON serialization
                json_data = [announcement.model_dump(mode='json') for announcement in data]

                # Write to file
                with open(self.output_file, "w", encoding="utf-8") as f:
                    if self.pretty_print:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                    else:
                        json.dump(json_data, f, ensure_ascii=False)

                logger.info(f"Saved {len(data)} announcements to {self.output_file}")

        except Exception as e:
            logger.error(f"Failed to save data to {self.output_file}: {e}")
            raise

    def _create_backup(self) -> None:
        """
        Create timestamped backup of current data file
        """
        if not self.output_file.exists():
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"master_backup_{timestamp}.json"

            # Copy current file to backup
            with open(self.output_file, "r", encoding="utf-8") as src:
                content = src.read()
            with open(backup_file, "w", encoding="utf-8") as dst:
                dst.write(content)

            logger.debug(f"Created backup: {backup_file}")

        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    def append_version(self, news_no: str, version: VersionEntry) -> None:
        """
        Append new version to an existing announcement

        Args:
            news_no: Announcement ID
            version: New version entry to append
        """
        data = self.load()

        # Find announcement by ID
        found = False
        for announcement in data:
            if announcement.id == news_no:
                announcement.version_history.append(version)
                found = True
                logger.info(f"Appended new version to announcement {news_no}")
                break

        if not found:
            logger.warning(f"Announcement {news_no} not found, cannot append version")
            return

        # Save updated data
        self.save(data)

    def add_announcement(self, announcement: Announcement) -> None:
        """
        Add new announcement to storage

        Args:
            announcement: Announcement object to add
        """
        data = self.load()

        # Check if announcement already exists
        for existing in data:
            if existing.id == announcement.id:
                logger.warning(f"Announcement {announcement.id} already exists, skipping add")
                return

        # Add new announcement
        data.append(announcement)
        logger.info(f"Added new announcement {announcement.id}")

        # Save updated data
        self.save(data)

    def get_by_id(self, news_no: str) -> Optional[Announcement]:
        """
        Get announcement by ID

        Args:
            news_no: Announcement ID

        Returns:
            Announcement object if found, None otherwise
        """
        data = self.load()
        for announcement in data:
            if announcement.id == news_no:
                return announcement
        return None
