"""
Content parser for extracting structured data from TRA announcements
"""

import re
import yaml
from typing import Optional
from pathlib import Path
from bs4 import BeautifulSoup
from loguru import logger

from src.models.announcement import ExtractedData
from src.utils.date_utils import parse_resumption_time


class ContentParser:
    """
    Parser for extracting structured data from announcement HTML
    """

    def __init__(self, config_path: str = "config/regex_patterns.yaml"):
        """
        Initialize content parser

        Args:
            config_path: Path to regex patterns configuration file
        """
        self.config_path = config_path
        self.patterns = self._load_patterns()

        # Event type keywords
        self.event_type_keywords = {
            "颱風": "Typhoon",
            "台風": "Typhoon",
            "豪雨": "Heavy_Rain",
            "大雨": "Heavy_Rain",
            "暴雨": "Heavy_Rain",
            "地震": "Earthquake",
            "落石": "Equipment_Failure",
            "出軌": "Equipment_Failure",
            "故障": "Equipment_Failure",
            "號誌": "Equipment_Failure",
            "電車線": "Equipment_Failure",
        }

        # Status keywords
        self.status_keywords = {
            "停駛": "Suspended",
            "暫停": "Suspended",
            "中斷": "Suspended",
            "暫停營運": "Suspended",
            "部分": "Partial_Operation",
            "單線": "Resumed_Single_Track",
            "單線行車": "Resumed_Single_Track",
            "恢復行駛": "Resumed_Normal",
            "恢復通車": "Resumed_Normal",
            "恢復營運": "Resumed_Normal",
            "已排除": "Resumed_Normal",
        }

    def _load_patterns(self) -> dict:
        """
        Load regex patterns from YAML configuration

        Returns:
            Dictionary of patterns
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load regex patterns from {self.config_path}: {e}")
            return {}

    def parse(self, html: str, publish_date: str, title: str = "") -> ExtractedData:
        """
        Parse HTML content and extract structured data

        Args:
            html: HTML content string
            publish_date: Announcement publish date in YYYY/MM/DD format
            title: Announcement title (optional, for better actual time extraction)

        Returns:
            ExtractedData object with extracted fields (None for failed extractions)
        """
        try:
            # Get text content from HTML
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(separator=" ", strip=True)

            # Extract all 7 fields
            report_version = self._extract_report_version(text)
            event_type = self._extract_event_type(text)
            status = self._extract_status(text)
            affected_lines = self._extract_affected_lines(text)
            affected_stations = self._extract_affected_stations(text)
            predicted_resumption_time = self._extract_predicted_time(text, publish_date)
            actual_resumption_time = self._extract_actual_time(text, publish_date, title)

            return ExtractedData(
                report_version=report_version,
                event_type=event_type,
                status=status,
                affected_lines=affected_lines,
                affected_stations=affected_stations,
                predicted_resumption_time=predicted_resumption_time,
                actual_resumption_time=actual_resumption_time,
            )

        except Exception as e:
            logger.debug(f"Error parsing content: {e}")
            return ExtractedData()

    def _extract_report_version(self, text: str) -> Optional[str]:
        """
        Extract report version number

        Args:
            text: Text content

        Returns:
            Report version string or None
        """
        try:
            patterns = self.patterns.get("report_version", [])
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
            return None
        except Exception as e:
            logger.debug(f"Failed to extract report_version: {e}")
            return None

    def _extract_event_type(self, text: str) -> Optional[str]:
        """
        Extract event type based on keywords

        Args:
            text: Text content

        Returns:
            Event type or None
        """
        try:
            for keyword, event_type in self.event_type_keywords.items():
                if keyword in text:
                    return event_type
            return None
        except Exception as e:
            logger.debug(f"Failed to extract event_type: {e}")
            return None

    def _extract_status(self, text: str) -> Optional[str]:
        """
        Extract operational status

        Args:
            text: Text content

        Returns:
            Status or None
        """
        try:
            for keyword, status in self.status_keywords.items():
                if keyword in text:
                    return status
            return None
        except Exception as e:
            logger.debug(f"Failed to extract status: {e}")
            return None

    def _extract_affected_lines(self, text: str) -> list:
        """
        Extract affected railway lines

        Args:
            text: Text content

        Returns:
            List of affected lines
        """
        try:
            lines = []
            railway_lines = self.patterns.get("railway_lines", [])
            for line in railway_lines:
                if line in text:
                    lines.append(line)
            return lines
        except Exception as e:
            logger.debug(f"Failed to extract affected_lines: {e}")
            return []

    def _extract_affected_stations(self, text: str) -> list:
        """
        Extract affected station names

        Args:
            text: Text content

        Returns:
            List of affected stations
        """
        try:
            pattern = self.patterns.get("station_pattern", r"([一-龥]{2,4})站")
            matches = re.findall(pattern, text)
            # Remove duplicates while preserving order
            stations = []
            seen = set()
            for station in matches:
                if station not in seen:
                    stations.append(station)
                    seen.add(station)
            return stations
        except Exception as e:
            logger.debug(f"Failed to extract affected_stations: {e}")
            return []

    def _extract_predicted_time(self, text: str, publish_date: str) -> Optional:
        """
        Extract predicted resumption time

        Args:
            text: Text content
            publish_date: Announcement publish date in YYYY/MM/DD format

        Returns:
            Datetime object or None
        """
        try:
            # Use date_utils for time parsing
            return parse_resumption_time(text, publish_date)
        except Exception as e:
            logger.debug(f"Failed to extract predicted_resumption_time: {e}")
            return None

    def _extract_actual_time(self, text: str, publish_date: str, title: str = "") -> Optional:
        """
        Extract actual resumption time

        Logic:
        1. If title contains "恢復正常行駛", "已恢復", "X時X分恢復通車" -> already resumed
        2. Try to extract actual time from content
        3. If no specific time found, use publish datetime from content
        4. If publish datetime not found, use publish_date end of day

        Args:
            text: Text content
            publish_date: Announcement publish date in YYYY/MM/DD format
            title: Announcement title

        Returns:
            Datetime object or None
        """
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo

            # Check if this is an "already resumed" announcement
            resumed_keywords = ['恢復正常行駛', '已恢復', '恢復通車', '恢復行駛']
            is_resumed = any(kw in title for kw in resumed_keywords)

            if not is_resumed:
                return None

            # Try to extract specific resumption time from title first (more accurate)
            # Pattern 0: From title - "今日X時起恢復" or "X時X分恢復通車"
            title_patterns = [
                r'(\d{1,2})[時:](\d{2})?(?:分)?(?:起)?.*?恢復',  # "8時起恢復", "8:00恢復"
                r'恢復.*?(\d{1,2})[時:](\d{2})?',  # "恢復...8時"
            ]
            for pattern in title_patterns:
                match = re.search(pattern, title)
                if match:
                    hour = int(match.group(1))
                    minute = int(match.group(2)) if match.group(2) else 0
                    ref_date = datetime.strptime(publish_date.replace("/", "-"), "%Y-%m-%d").replace(tzinfo=ZoneInfo("Asia/Taipei"))
                    return ref_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # Try to extract specific resumption time from content
            # Pattern 1: "X時起恢復" or "已於X時X分恢復" or "恢復...X時"
            content_patterns = [
                r'(\d{1,2})[時:](\d{2})?(?:分)?起.*?恢復',  # "8時起恢復"
                r'(?:已[於在]).*?(\d{1,2})[時:](\d{2})',  # "已於8時恢復"
                r'恢復.*?(\d{1,2})[時:](\d{2})',  # "恢復...8:00"
            ]
            for pattern in content_patterns:
                match = re.search(pattern, text)
                if match:
                    hour = int(match.group(1))
                    minute = int(match.group(2)) if match.group(2) else 0
                    ref_date = datetime.strptime(publish_date.replace("/", "-"), "%Y-%m-%d").replace(tzinfo=ZoneInfo("Asia/Taipei"))
                    return ref_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # Pattern 2: Try to extract publish datetime from content (e.g., "發佈日期：2025/9/24 下午 9:40")
            publish_time_pattern = r'發[佈布]日期[：:].{0,20}?[上下]午\s*(\d{1,2})[：:](\d{2})'
            match = re.search(publish_time_pattern, text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                # Adjust for 下午 (PM)
                if '下午' in text[max(0, match.start()-5):match.end()]:
                    if hour < 12:
                        hour += 12
                ref_date = datetime.strptime(publish_date.replace("/", "-"), "%Y-%m-%d").replace(tzinfo=ZoneInfo("Asia/Taipei"))
                return ref_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # Fallback: Use end of publish_date
            ref_date = datetime.strptime(publish_date.replace("/", "-"), "%Y-%m-%d").replace(tzinfo=ZoneInfo("Asia/Taipei"))
            return ref_date.replace(hour=23, minute=59, second=59, microsecond=0)

        except Exception as e:
            logger.debug(f"Failed to extract actual_resumption_time: {e}")
            return None
