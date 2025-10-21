"""
Date and time parsing utilities for TRA announcements
"""

import re
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo
from loguru import logger


# Timezone for Taiwan
TAIPEI_TZ = ZoneInfo("Asia/Taipei")


def parse_tra_date(date_str: str) -> str:
    """
    Parse TRA date format (YYYY/MM/DD) to ISO 8601 format

    Args:
        date_str: Date string in format "YYYY/MM/DD"

    Returns:
        ISO 8601 date string (YYYY-MM-DD)

    Examples:
        >>> parse_tra_date("2025/10/21")
        '2025-10-21'
    """
    try:
        # Replace slashes with hyphens for ISO format
        return date_str.replace("/", "-")
    except Exception as e:
        logger.debug(f"Failed to parse TRA date '{date_str}': {e}")
        return date_str


def parse_resumption_time(text: str) -> Optional[datetime]:
    """
    Parse resumption time from Chinese text using regex patterns

    Handles formats like:
    - "今日19:00"
    - "明日凌晨"
    - "8月13日12時前"
    - "預計於今日19:00恢復行駛"

    Args:
        text: HTML or text content containing time information

    Returns:
        Timezone-aware datetime object (Asia/Taipei) or None if parsing fails

    Examples:
        >>> parse_resumption_time("預計於今日19:00恢復行駛")
        datetime(2025, 10, 21, 19, 0, tzinfo=ZoneInfo('Asia/Taipei'))
    """
    if not text:
        return None

    try:
        now = datetime.now(TAIPEI_TZ)

        # Pattern 1: 今日 HH:MM or 今日HH:MM
        pattern1 = r'今日\s*(\d{1,2})[：:時](\d{2})?'
        match = re.search(pattern1, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Pattern 2: 明日 HH:MM or 明日HH:MM
        pattern2 = r'明日\s*(\d{1,2})[：:時](\d{2})?'
        match = re.search(pattern2, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Pattern 3: M月D日 HH時 or M月D日HH時
        pattern3 = r'(\d{1,2})月(\d{1,2})日\s*(\d{1,2})[時:](\d{2})?'
        match = re.search(pattern3, text)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            hour = int(match.group(3))
            minute = int(match.group(4)) if match.group(4) else 0
            # Assume current year or next year if month is in the past
            year = now.year
            try:
                result = datetime(year, month, day, hour, minute, tzinfo=TAIPEI_TZ)
                if result < now:
                    # If date is in the past, try next year
                    result = datetime(year + 1, month, day, hour, minute, tzinfo=TAIPEI_TZ)
                return result
            except ValueError:
                logger.debug(f"Invalid date: {year}/{month}/{day} {hour}:{minute}")
                return None

        # Pattern 4: 今日 (without specific time, default to end of day)
        if '今日' in text and not re.search(pattern1, text):
            return now.replace(hour=23, minute=59, second=59, microsecond=0)

        # Pattern 5: 明日 (without specific time)
        if '明日' in text and not re.search(pattern2, text):
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=23, minute=59, second=59, microsecond=0)

        # Pattern 6: 凌晨 (early morning, assume 5:00 AM)
        if '凌晨' in text:
            if '明日' in text or '明天' in text:
                tomorrow = now + timedelta(days=1)
                return tomorrow.replace(hour=5, minute=0, second=0, microsecond=0)
            else:
                return now.replace(hour=5, minute=0, second=0, microsecond=0)

        # Pattern 7: Standard time HH:MM or HH:MM format
        pattern7 = r'(\d{1,2})[：:時](\d{2})'
        match = re.search(pattern7, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            result = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            # If time is in the past today, assume tomorrow
            if result < now:
                result = result + timedelta(days=1)
            return result

        logger.debug(f"No resumption time pattern matched in text: {text[:100]}...")
        return None

    except Exception as e:
        logger.debug(f"Error parsing resumption time from '{text[:100]}...': {e}")
        return None
