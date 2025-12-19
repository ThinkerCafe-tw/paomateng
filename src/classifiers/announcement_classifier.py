"""
Classifier for categorizing TRA announcements
"""

import re
import yaml
from typing import List
from loguru import logger

from src.models.announcement import Classification


class AnnouncementClassifier:
    """
    Classifier for categorizing announcements based on keyword matching
    """

    def __init__(self, config_path: str = "config/keywords.yaml"):
        """
        Initialize classifier

        Args:
            config_path: Path to keywords configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """
        Load keywords configuration from YAML

        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, "r", encoding="utf-8")  as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load keywords from {self.config_path}: {e}")
            return {"categories": {}, "default_category": "General_Operation"}

    def classify(self, title: str, content: str) -> Classification:
        """
        Classify announcement based on title and content

        Uses a two-layer approach:
        1. First check title for disruption indicators (title is the "soul" of announcement)
        2. If no disruption indicators in title, skip Disruption classification entirely

        Args:
            title: Announcement title
            content: Announcement content

        Returns:
            Classification object with category, keywords, and event_group_id
        """
        # === 第一層：標題優先判斷 ===
        # 停駛相關核心詞（必須出現在標題才進入 Disruption 流程）
        disruption_indicators = [
            '停駛', '暫停', '中斷', '延誤', '故障', '搶修', '恢復',
            '落石', '出軌', '號誌', '事故', '搶通', '影響', '受損',
            '第1報', '第2報', '第3報', '第4報', '第5報',
            '第1發', '第2發', '第3發', '第4發', '第5發',
        ]

        title_has_disruption = any(word in title for word in disruption_indicators)

        # 如果標題沒有任何停駛相關詞，只檢查是否為天氣相關
        if not title_has_disruption:
            # 檢查是否為天氣相關公告（颱風、豪雨等）
            weather_keywords = self.config.get("categories", {}).get("Weather_Related", {}).get("keywords", [])
            matched_weather = [kw for kw in weather_keywords if kw in title]

            if matched_weather:
                return Classification(
                    category="Weather_Related",
                    keywords=matched_weather,
                    event_group_id=self.extract_event_group_id(title, "")
                )

            # 標題沒有停駛相關詞，也不是天氣相關 → 直接分為 General_Operation
            return Classification(
                category="General_Operation",
                keywords=[],
                event_group_id=self.extract_event_group_id(title, "")
            )

        # === 第二層：原有的關鍵字匹配邏輯（只有標題包含停駛詞才會進入）===
        # Combine title and content for keyword matching
        text = f"{title} {content}"

        # Find matched keywords and determine category
        matched_keywords = []
        category = self.config.get("default_category", "General_Operation")

        categories = self.config.get("categories", {})

        # Priority order for categories (check resumption LAST to override earlier matches)
        priority_order = [
            "Disruption_Suspension",
            "Disruption_Update",
            "Weather_Related",
            "Disruption_Resumption",  # Check resumption last - highest priority
        ]

        for cat_name in priority_order:
            if cat_name in categories:
                keywords = categories[cat_name].get("keywords", [])
                for keyword in keywords:
                    if keyword in text:
                        matched_keywords.append(keyword)

                # If any keywords matched for this category, update category
                # Allow override if this is a higher priority category (later in list)
                if matched_keywords and any(k in text for k in keywords):
                    category = cat_name

        # Remove duplicates from matched keywords
        matched_keywords = list(dict.fromkeys(matched_keywords))

        # Extract event group ID
        event_group_id = self.extract_event_group_id(title, "")

        return Classification(
            category=category,
            keywords=matched_keywords,
            event_group_id=event_group_id,
        )

    def extract_event_group_id(self, title: str, publish_date: str) -> str:
        """
        Extract event group ID from title and publish date

        Args:
            title: Announcement title
            publish_date: Publish date in YYYY/MM/DD format

        Returns:
            Event group ID in format "YYYYMMDD_EventName"
        """
        try:
            # Extract date in YYYYMMDD format
            date_part = ""
            if publish_date:
                date_part = publish_date.replace("/", "")
            else:
                # Try to extract from title or use placeholder
                date_match = re.search(r"(\d{4})/(\d{2})/(\d{2})", title)
                if date_match:
                    date_part = f"{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}"
                else:
                    date_part = "UNKNOWN"

            # Extract event name from title
            event_name = self._extract_event_name(title)

            return f"{date_part}_{event_name}"

        except Exception as e:
            logger.debug(f"Failed to extract event_group_id: {e}")
            return "UNKNOWN_Event"

    def _extract_event_name(self, title: str) -> str:
        """
        Extract event name from title

        Args:
            title: Announcement title

        Returns:
            Event name string
        """
        try:
            # Remove common prefixes and report numbers
            cleaned_title = title

            # Remove report numbers
            cleaned_title = re.sub(r"第\d+[報發次]", "", cleaned_title)

            # Remove time information
            cleaned_title = re.sub(r"\d{1,2}:\d{2}", "", cleaned_title)
            cleaned_title = re.sub(r"\d{1,2}[時點]", "", cleaned_title)

            # Common event patterns
            event_patterns = [
                r"([\w]+颱風)",  # Typhoon names
                r"([\w]+豪雨)",  # Heavy rain events
                r"([\w]+地震)",  # Earthquake
                r"([一-龥]+線)",  # Railway line names
                r"([一-龥]{2,6}站)",  # Station names
            ]

            for pattern in event_patterns:
                match = re.search(pattern, cleaned_title)
                if match:
                    return match.group(1).replace(" ", "_")

            # If no specific pattern matched, clean up and use title
            # Remove special characters and spaces
            event_name = re.sub(r"[^\w一-龥]", "_", cleaned_title.strip())
            event_name = re.sub(r"_+", "_", event_name)  # Remove consecutive underscores
            event_name = event_name.strip("_")

            # Limit length
            if len(event_name) > 30:
                event_name = event_name[:30]

            return event_name if event_name else "General"

        except Exception as e:
            logger.debug(f"Failed to extract event name: {e}")
            return "General"
