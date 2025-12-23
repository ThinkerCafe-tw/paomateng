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

            # NEW: Check if this is a non-train announcement (e.g., IT system maintenance)
            # These should NOT be parsed for train-related fields
            if self._is_non_train_announcement(title, text):
                logger.debug(f"Skipping extraction for non-train announcement: {title[:50]}")
                return ExtractedData()

            # Extract all 7 fields
            report_version = self._extract_report_version(text)
            event_type = self._extract_event_type(text)
            status = self._extract_status(text, title)  # Pass title for context
            affected_lines = self._extract_affected_lines(text)
            affected_stations = self._extract_affected_stations(text)
            predicted_resumption_time = self._extract_predicted_time(text, publish_date, title)
            actual_resumption_time = self._extract_actual_time(text, publish_date, title)

            # NEW: Identify service type if actual resumption time exists
            service_type = None
            service_details = None
            if actual_resumption_time:
                service_type, service_details = self._identify_service_type(text, title)

            return ExtractedData(
                report_version=report_version,
                event_type=event_type,
                status=status,
                affected_lines=affected_lines,
                affected_stations=affected_stations,
                predicted_resumption_time=predicted_resumption_time,
                actual_resumption_time=actual_resumption_time,
                service_type=service_type,
                service_details=service_details,
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

    def _is_non_train_announcement(self, title: str, text: str) -> bool:
        """
        Check if this is a non-train-related announcement that should be skipped.

        Examples of non-train announcements:
        - IT system maintenance (系統維護公告)
        - Website service announcements (官網服務)
        - Ticketing system notices (訂票系統)

        Args:
            title: Announcement title
            text: Text content

        Returns:
            True if this is NOT a train-related announcement
        """
        # System maintenance announcements
        system_keywords = [
            '系統維護',
            '系統停機',
            '網站維護',
            '網站服務',
            '訂票系統',
            '訂位系統',
            '會員服務系統',
            'e訂通',
        ]

        # Check title first (most reliable)
        for keyword in system_keywords:
            if keyword in title:
                logger.debug(f"Non-train announcement detected (title keyword: {keyword})")
                return True

        # Check if content is about IT systems, NOT train operations
        # Must have system keywords AND no train operation keywords
        train_operation_keywords = [
            '列車', '班車', '停駛', '通車', '行駛',
            '路線', '鐵路', '軌道', '月台',
        ]

        has_system_keyword = any(kw in text for kw in system_keywords)
        has_train_keyword = any(kw in text for kw in train_operation_keywords)

        # If it has system keywords but NO train keywords, skip it
        if has_system_keyword and not has_train_keyword:
            # Double-check: "暫停官網網站服務" should be skipped
            if '暫停官網' in text or '暫停網站' in text:
                logger.debug(f"Non-train announcement detected (website service suspension)")
                return True

        return False

    def _extract_status(self, text: str, title: str = "") -> Optional[str]:
        """
        Extract operational status with context awareness

        Args:
            text: Text content
            title: Announcement title for context

        Returns:
            Status or None
        """
        try:
            for keyword, status in self.status_keywords.items():
                if keyword in text:
                    # NEW: Context check to avoid false positives
                    # "暫停官網網站服務" should NOT trigger "Suspended" for trains
                    if keyword == "暫停":
                        # Check if "暫停" is followed by non-train services
                        non_train_contexts = [
                            r'暫停官網',
                            r'暫停網站',
                            r'暫停.*?服務系統',
                            r'暫停.*?訂[票位]',
                            r'暫停.*?e訂通',
                        ]
                        is_non_train = any(re.search(pattern, text) for pattern in non_train_contexts)

                        if is_non_train:
                            # Check if there's also train-related suspension
                            train_suspension_patterns = [
                                r'暫停營運',
                                r'暫停行駛',
                                r'列車.*?暫停',
                                r'暫停.*?列車',
                            ]
                            has_train_suspension = any(re.search(pattern, text) for pattern in train_suspension_patterns)

                            if not has_train_suspension:
                                logger.debug(f"Skipping status 'Suspended' - non-train context: {keyword}")
                                continue  # Skip this keyword, try next

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

            # NEW: Blacklist for false positives
            # These are NOT train stations but contain the character "站"
            station_blacklist = {
                # IT/Website related
                '官網網',      # 官網網站
                '停官網網',    # 暫停官網網站
                '網',          # 網站
                '官網',        # 官網站 (unlikely but possible)
                # Service related
                '服務',        # 服務站 (not a train station name)
                '加油',        # 加油站
                '充電',        # 充電站
                '休息',        # 休息站
                # Other false positives
                '車',          # 車站 (too generic)
                '總',          # 總站 (too generic without context)
                '本',          # 本站
                '各',          # 各站
                '每',          # 每站
                '全',          # 全站
            }

            # Remove duplicates while preserving order, and filter blacklist
            stations = []
            seen = set()
            for station in matches:
                if station not in seen and station not in station_blacklist:
                    stations.append(station)
                    seen.add(station)
            return stations
        except Exception as e:
            logger.debug(f"Failed to extract affected_stations: {e}")
            return []

    def _extract_predicted_time(self, text: str, publish_date: str, title: str = "") -> Optional:
        """
        Extract predicted resumption time

        IMPORTANT: This should extract ONLY predicted/planned times, NOT actual completion times
        If the text contains completion indicators (已於...恢復, 於...搶修完成), skip extraction

        Args:
            text: Text content
            publish_date: Announcement publish date in YYYY/MM/DD format
            title: Announcement title (for context-based filtering)

        Returns:
            Datetime object or None
        """
        try:
            # NEW: Title-based context filtering to reduce False Positives
            # These filters prevent extraction from non-resumption announcements

            # Filter 1: Typhoon suspension announcements (颱風停駛公告)
            # Example: "臺鐵公司因應丹娜絲颱風列車行駛資訊 第2報"
            # These announce suspension times, NOT resumption predictions
            if "列車行駛資訊" in title and not any(kw in title for kw in ["恢復", "復駛"]):
                logger.debug(f"Skipping predicted extraction: typhoon suspension announcement without resumption")
                return None

            # Filter 2: Repair progress reports (搶修進度報告)
            # Example: "強降雨致北迴線雙向中斷路線受損概況 第2發"
            # These report repair status, NOT resumption predictions (unless explicitly stated)
            repair_report_keywords = ["搶修概況", "受損概況", "疏運應變措施", "提前搶通", "路線受損"]
            resumption_prediction_keywords = ["預計恢復", "預估恢復"]

            if any(kw in title for kw in repair_report_keywords):
                if not any(kw in title for kw in resumption_prediction_keywords):
                    logger.debug(f"Skipping predicted extraction: repair progress report without resumption prediction")
                    return None

            # Filter 3: Shuttle service announcements (接駁服務通知)
            # Example: "強降雨影響北迴線路線受損搶修復原及旅客疏運最新概況 第6發"
            # Shuttle start time ≠ train resumption time
            shuttle_keywords = ["疏運", "接駁"]
            if any(kw in title for kw in shuttle_keywords):
                if not any(kw in title for kw in ["列車恢復", "恢復行駛", "恢復通車"]):
                    logger.debug(f"Skipping predicted extraction: shuttle service announcement without train resumption")
                    return None
            # Check if this text contains actual completion indicators
            # If so, this should be extracted as actual time, not predicted
            # IMPORTANT: These patterns must match COMPLETION events, not preparation/start events
            # IMPORTANT: Exception - if there's explicit "預計" in the text, we should still try to extract predicted time
            #            (for phased recovery: "已於16:48恢復單線，預計18時恢復雙線")
            actual_completion_patterns = [
                r'已[於在][^。]{0,50}?恢復',  # "已於X時X分恢復"
                r'於[今本]\(?(\d+)?\)?日\s*\d{1,2}[：:時](?:\d{2})?(?:起|分)?[^。]{0,20}?恢復',  # "於今(24)日8時起...恢復" (confirmed resumption)
                r'於\s*\d{1,2}[：:時]\d{2}(?:分)?[^。]{0,10}?恢復(?:雙向)?通車',  # "於16:50恢復通車" (stricter: within 10 chars)
                r'於\s*\d{1,2}[：:時]\d{2}(?:分)?\s*搶修完[成畢]',  # "於17:10搶修完成" (stricter: immediate adjacency)
                r'\d{1,2}[：:時]\d{2}(?:分)?[^。]{0,10}?恢復(?:雙向)?通車',  # "17:00恢復雙向通車" (without 於)
                r'今\(\d+\)日\s*\d{1,2}[：:時]\d{2}(?:分)?起[^。]{0,30}?鐵路接駁服務',  # "今(19)日05:32起...鐵路接駁服務" (actual shuttle start)
            ]

            # Check if text has explicit prediction keywords (預計/預估)
            has_explicit_prediction = re.search(r'預計|預估', text)

            for pattern in actual_completion_patterns:
                match = re.search(pattern, text)
                if match:
                    # Double-check this is NOT a prediction (no 預計/預估 within 20 chars before)
                    context_before = text[max(0, match.start()-20):match.start()]
                    if not re.search(r'預計|預估', context_before):
                        # If there's no explicit prediction elsewhere in text, skip predicted extraction
                        if not has_explicit_prediction:
                            logger.debug(f"Skipping predicted extraction due to actual completion indicator: {pattern}")
                            return None
                        # Otherwise, continue to try extracting predicted time (phased recovery case)

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
            # Must have resumption keywords in title OR content
            # IMPORTANT: Content must have "已於...恢復" or "於...恢復" (NOT just "預計...恢復")
            resumed_keywords_title = ['恢復正常行駛', '已恢復', '恢復通車', '恢復行駛']
            # Match ACTUAL resumption patterns in content (completion events, not predictions)
            # IMPORTANT: Use strict patterns to avoid matching preparation/start events
            # IMPORTANT: "今日X時起...鐵路接駁服務" counts as partial resumption (actual)
            resumed_keywords_content = [
                r'已[於在][^。]{0,50}?恢復',  # "已於X時X分恢復"
                r'搶修完畢[^。]{0,30}?恢復',  # "搶修完畢...恢復"
                r'於\s*\d{1,2}[：:時]\d{2}(?:分)?[^。]{0,10}?恢復(?:雙向)?通車',  # "於16:50恢復通車" (stricter: within 10 chars)
                r'於\s*\d{1,2}[：:時]\d{2}(?:分)?\s*搶修完[成畢]',  # "於17:10搶修完成" (stricter: immediate adjacency)
                r'\d{1,2}[：:時]\d{2}(?:分)?[^。]{0,10}?恢復(?:雙向)?通車',  # "17:00恢復雙向通車" (without 於)
                r'今\(\d+\)日\s*\d{1,2}[：:時]\d{2}(?:分)?起[^。]{0,30}?鐵路接駁服務',  # "今(19)日05:32起...鐵路接駁服務" (actual shuttle start)
            ]

            has_resumption_in_title = any(kw in title for kw in resumed_keywords_title)
            has_resumption_in_content = any(re.search(pattern, text) for pattern in resumed_keywords_content)

            # IMPORTANT: Exclude predictions even if pattern matches
            # Must NOT have "預計" within 20 chars before the time pattern
            # IMPORTANT: Exclude conditional statements like "確認...後，恢復" (not yet resumed)
            if has_resumption_in_content:
                # Check for prediction indicators before the matched pattern
                prediction_indicators = [r'預計', r'預估']
                # Check for conditional indicators: "...後，恢復" or "...後恢復"
                conditional_indicators = [r'後[，,\s]{0,2}恢復', r'俟.*?後.*?恢復']

                for pattern in resumed_keywords_content:
                    match = re.search(pattern, text)
                    if match:
                        matched_text = match.group(0)
                        context_before = text[max(0, match.start()-20):match.start()]

                        # Check for prediction indicators
                        if any(re.search(indicator, context_before) for indicator in prediction_indicators):
                            has_resumption_in_content = False
                            break

                        # Check for conditional statements (future, not completed)
                        # "確認安全無虞後，恢復行車" = will resume AFTER confirmation (not yet resumed)
                        if any(re.search(indicator, matched_text) for indicator in conditional_indicators):
                            has_resumption_in_content = False
                            break

            if not has_resumption_in_title and not has_resumption_in_content:
                return None

            # Check if this is a FUTURE announcement (not already resumed)
            future_indicators = [
                r'明\(\d+\)日.*恢復',  # "明(24)日...恢復"
                r'明日.*恢復',  # "明日...恢復"
                r'\d+日.*恢復',  # "24日...恢復" (without 今日)
                r'預計.*恢復',  # "預計...恢復"
            ]

            # If title contains future indicators, this is NOT an actual resumption
            for pattern in future_indicators:
                if re.search(pattern, title):
                    return None  # This is predicted, not actual

            # Try to extract specific resumption time from title first (more accurate)
            # Pattern 0: From title - various formats

            # NEW: Pattern 0a - "於今(X)日Y時起恢復" (Fix for Actual False Negative)
            # Example: "臺鐵公司於今(24)日8時起臺東線列車恢復正常行駛 第8報"
            pattern_0a = r'於[今本]\((\d+)\)日\s*(\d{1,2})[時:](\d{2})?起.*?恢復'
            match = re.search(pattern_0a, title)
            if match:
                day = int(match.group(1))
                hour = int(match.group(2))
                minute = int(match.group(3)) if match.group(3) else 0
                ref_date = datetime.strptime(publish_date.replace("/", "-"), "%Y-%m-%d").replace(tzinfo=ZoneInfo("Asia/Taipei"))
                try:
                    return ref_date.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
                except ValueError:
                    pass  # Invalid date, fall through to other patterns

            # Pattern 0b - "今日X時起恢復" or "X時X分恢復通車"
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
            # IMPORTANT: Time must be CLOSE to "恢復" (within reasonable distance)
            # Allow commas, but limit total distance to avoid matching across events
            # Priority: full recovery > partial recovery > other completions
            content_patterns = [
                # High priority: Full recovery (恢復雙向通車)
                (r'(\d{1,2})[時:](\d{2})(?:分)?[^。]{0,15}?恢復(?:雙向)?通車', 'full_recovery'),
                # Medium priority: Repair completion
                (r'於\s*(\d{1,2})[時:](\d{2})(?:分)?[^。]{0,15}?搶修完[成畢]', 'repair_completion'),
                # Medium priority: Shuttle service start (鐵路接駁服務開始)
                (r'今\(\d+\)日\s*(\d{1,2})[時:](\d{2})(?:分)?起[^。]{0,30}?鐵路接駁', 'shuttle_start'),
                # Lower priority: General resumption
                (r'(\d{1,2})[時:](\d{2})(?:分)?起[^。]{0,10}?恢復', 'general'),
                (r'於\s*(\d{1,2})[時:](\d{2})(?:分)?[^。]{0,15}?恢復', 'general'),
                (r'已[於在][^。]{0,15}?(\d{1,2})[時:](\d{2})(?:分)?[^。]{0,15}?恢復', 'general'),
            ]

            earliest_time = None

            for pattern, priority_name in content_patterns:
                for match in re.finditer(pattern, text):
                    # Check context for prediction indicators (預計)
                    context_before = text[max(0, match.start()-20):match.start()]
                    if re.search(r'預計|預估', context_before):
                        continue

                    hour = int(match.group(1))
                    minute = int(match.group(2)) if match.group(2) else 0
                    current_time = (hour, minute)

                    # For actual resumption, prefer EARLIEST time (when service first resumes)
                    # Example: "16:50恢復單線雙向通車，17:00恢復雙向通車" → extract 16:50
                    if earliest_time is None or current_time < earliest_time:
                        earliest_time = current_time

            if earliest_time:
                hour, minute = earliest_time
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

    def _identify_service_type(self, text: str, title: str = "") -> tuple[Optional[str], Optional[str]]:
        """
        Identify the type of service resumption

        Args:
            text: Text content
            title: Announcement title

        Returns:
            Tuple of (service_type, service_details)
            service_type can be:
            - 'shuttle_service': 接駁服務 (temporary shuttle)
            - 'partial_operation': 部分營運 (partial service, single track, etc.)
            - 'normal_train': 正常列車服務 (normal train service)
            - None: if cannot determine
        """
        try:
            # Combine title and text for analysis
            full_text = f"{title} {text}"

            # IMPORTANT: Check title first - if title explicitly says "恢復通車" or "恢復行駛",
            # this is likely normal/partial operation, NOT shuttle service
            # Shuttle service is usually explicitly stated in title as "接駁服務" or "接駁開始"
            title_resumption = bool(re.search(r'恢復.*?通車|恢復.*?行駛|恢復正常|恢復營運', title))
            title_shuttle = any(pattern in title for pattern in ['接駁服務', '接駁開始', '鐵路接駁'])

            # If title says resumption but not shuttle, skip shuttle check
            skip_shuttle_check = title_resumption and not title_shuttle

            # Also check for cancellation/termination of shuttle service
            # If shuttle is cancelled, this is NOT shuttle service resumption
            cancellation_patterns = [
                r'取消.*?接駁',
                r'停止.*?接駁',
                r'結束.*?接駁',
            ]

            shuttle_cancelled = any(re.search(pattern, full_text) for pattern in cancellation_patterns)

            # Priority 1: Check for shuttle service (接駁服務)
            # BUT skip if:
            # 1. Shuttle was cancelled in this announcement, OR
            # 2. Title explicitly says service resumption (not shuttle)
            # Keywords: 接駁, 柴聯車, 公路接駁, 巴士接駁
            shuttle_patterns = [
                r'接駁服務',
                r'鐵路接駁',
                r'公路接駁',
                r'柴聯車.*?接駁',
                r'接駁.*?柴聯車',
                r'巴士接駁',
                r'接駁巴士',
            ]

            # Only identify as shuttle service if NOT cancelled AND NOT skipped
            if not shuttle_cancelled and not skip_shuttle_check:
                for pattern in shuttle_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        # Extract details
                        details = None

                        # Try to find specific shuttle type
                        if '柴聯車' in full_text:
                            details = '柴聯車接駁'
                        elif '公路' in full_text or '巴士' in full_text:
                            details = '公路/巴士接駁'
                        else:
                            details = '鐵路接駁服務'

                        logger.debug(f"Identified service_type: shuttle_service ({details})")
                        return ('shuttle_service', details)
            elif shuttle_cancelled:
                logger.debug(f"Shuttle service mentioned but cancelled - not shuttle_service")
            elif skip_shuttle_check:
                logger.debug(f"Title indicates train resumption - skipping shuttle check")

            # Priority 2: Check for partial operation (部分營運)
            # Keywords: 單線, 部分, 局部, 區間
            partial_patterns = [
                (r'單線雙向通車', '單線雙向通車'),
                (r'單線.*?行車', '單線行車'),
                (r'部分.*?恢復', '部分恢復'),
                (r'局部.*?通車', '局部通車'),
                (r'區間.*?恢復', '區間恢復'),
            ]

            for pattern, detail in partial_patterns:
                if re.search(pattern, full_text):
                    logger.debug(f"Identified service_type: partial_operation ({detail})")
                    return ('partial_operation', detail)

            # Priority 3: Check for normal service resumption
            # Keywords: 恢復正常, 恢復行駛, 恢復通車, 正常行駛
            normal_patterns = [
                r'恢復正常',
                r'正常行駛',
                r'正常營運',
                r'恢復雙向通車',
                r'恢復行駛',
                r'恢復通車',
            ]

            for pattern in normal_patterns:
                if re.search(pattern, full_text):
                    logger.debug(f"Identified service_type: normal_train")
                    return ('normal_train', '正常列車服務')

            # Default: If we have actual_resumption_time but can't classify, default to normal_train
            # This is a conservative assumption
            logger.debug(f"Service type unclear, defaulting to: normal_train")
            return ('normal_train', None)

        except Exception as e:
            logger.debug(f"Failed to identify service_type: {e}")
            return (None, None)
