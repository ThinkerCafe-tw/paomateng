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

    def parse(self, html: str, publish_date: str) -> ExtractedData:
        """
        Parse HTML content and extract structured data

        Args:
            html: HTML content string
            publish_date: Announcement publish date in YYYY/MM/DD format

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
            actual_resumption_time = self._extract_actual_time(text, publish_date)

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

    def _extract_actual_time(self, text: str, publish_date: str) -> Optional:
        """
        Extract actual resumption time

        Args:
            text: Text content
            publish_date: Announcement publish date in YYYY/MM/DD format

        Returns:
            Datetime object or None
        """
        try:
            # Look for phrases indicating actual resumption
            if "已於" in text or "已在" in text or "已恢復" in text:
                # Try to extract time after these phrases
                pattern = r"已[於在].*?(\d{1,2})[：:時](\d{2})"
                match = re.search(pattern, text)
                if match:
                    # Use parse_resumption_time to get timezone-aware datetime
                    time_str = f"{match.group(1)}:{match.group(2)}"
                    return parse_resumption_time(time_str, publish_date)
            return None
        except Exception as e:
            logger.debug(f"Failed to extract actual_resumption_time: {e}")
            return None
