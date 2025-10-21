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


def parse_resumption_time(text: str, publish_date: str) -> Optional[datetime]:
    """
    Parse resumption time from Chinese text using regex patterns

    Handles formats like:
    - "今日19:00"
    - "明日凌晨"
    - "8月13日12時前"
    - "預計於今日19:00恢復行駛"

    Args:
        text: HTML or text content containing time information
        publish_date: Announcement publish date in YYYY/MM/DD format (used as reference date)

    Returns:
        Timezone-aware datetime object (Asia/Taipei) or None if parsing fails

    Examples:
        >>> parse_resumption_time("預計於今日19:00恢復行駛", "2025/08/13")
        datetime(2025, 8, 13, 19, 0, tzinfo=ZoneInfo('Asia/Taipei'))
    """
    if not text:
        return None

    try:
        # Use publish_date as reference, NOT today's date
        ref_date_str = publish_date.replace("/", "-")
        ref_date = datetime.strptime(ref_date_str, "%Y-%m-%d").replace(tzinfo=TAIPEI_TZ)

        # Pattern 1: 今日 HH:MM or 今日HH:MM
        pattern1 = r'今日\s*(\d{1,2})[：:時](\d{2})?'
        match = re.search(pattern1, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            return ref_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Pattern 2: 明日 HH:MM or 明日HH:MM
        pattern2 = r'明日\s*(\d{1,2})[：:時](\d{2})?'
        match = re.search(pattern2, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            tomorrow = ref_date + timedelta(days=1)
            return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Pattern 3: M月D日 HH時 with context (must have keywords nearby)
        # Only extract if date appears near resumption keywords
        resumption_keywords_p3 = ['預計', '恢復', '復駛', '通車', '修復完成', '營運']
        for keyword in resumption_keywords_p3:
            # Look for date within 30 characters after resumption keyword
            pattern3 = rf'{keyword}.{{0,30}}?(\d{{1,2}})月(\d{{1,2}})日\s*(\d{{1,2}})[時:](\d{{2}})?'
            match = re.search(pattern3, text)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                hour = int(match.group(3))
                minute = int(match.group(4)) if match.group(4) else 0
                # Use reference year from publish_date
                year = ref_date.year
                try:
                    result = datetime(year, month, day, hour, minute, tzinfo=TAIPEI_TZ)
                    # If date is before publish_date, it's likely historical info - don't extract
                    if result < ref_date:
                        logger.debug(f"Date {result} is before publish_date {ref_date}, skipping")
                        continue
                    return result
                except ValueError:
                    logger.debug(f"Invalid date: {year}/{month}/{day} {hour}:{minute}")
                    continue

        # Pattern 4: 今日 (without specific time, default to end of day)
        if '今日' in text and not re.search(pattern1, text):
            return ref_date.replace(hour=23, minute=59, second=59, microsecond=0)

        # Pattern 5: 明日 (without specific time)
        if '明日' in text and not re.search(pattern2, text):
            tomorrow = ref_date + timedelta(days=1)
            return tomorrow.replace(hour=23, minute=59, second=59, microsecond=0)

        # Pattern 6: 凌晨 (early morning, assume 5:00 AM)
        if '凌晨' in text:
            if '明日' in text or '明天' in text:
                tomorrow = ref_date + timedelta(days=1)
                return tomorrow.replace(hour=5, minute=0, second=0, microsecond=0)
            else:
                return ref_date.replace(hour=5, minute=0, second=0, microsecond=0)

        # Pattern 7: Time with context (must have keywords like "預計", "恢復", "復駛" nearby)
        # Only extract if time appears in resumption context
        resumption_keywords = ['預計', '恢復', '復駛', '通車', '營運', '行駛']
        for keyword in resumption_keywords:
            # Look for time within 20 characters after resumption keyword
            pattern = rf'{keyword}.{{0,20}}?(\d{{1,2}})[：:時](\d{{2}})'
            match = re.search(pattern, text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                return ref_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        logger.debug(f"No resumption time pattern matched in text: {text[:100]}...")
        return None

    except Exception as e:
        logger.debug(f"Error parsing resumption time from '{text[:100]}...': {e}")
        return None
