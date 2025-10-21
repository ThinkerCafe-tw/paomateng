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
    - "明日首班車"
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

        # Remove "發佈日期" section to avoid extracting publish time as resumption time
        text = re.sub(r'發[佈布]日期[：:][^。\n]*[。\n]?', '', text)

        # Remove "發生時間" section to avoid extracting incident time as resumption time
        # Only remove until sentence end (。) or newline to avoid over-removal
        text = re.sub(r'發生時間[：:][^。\n]*[。\n]?', '', text)

        # Pattern 1: 今日 HH:MM or 今日HH:MM
        pattern1 = r'今日\s*(\d{1,2})[：:時](\d{2})?'
        match = re.search(pattern1, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            return ref_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Pattern 2: 明日 HH:MM or 明日HH:MM or 明(X)日HH:MM
        pattern2 = r'明(?:\(\d+\))?日\s*(\d{1,2})[：:時](\d{2})?'
        match = re.search(pattern2, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            tomorrow = ref_date + timedelta(days=1)
            return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Pattern 2.5: 明日首班車 or 今日首班車 or M月D日首班車 (first train, assume 5:30 AM)
        if re.search(r'(?:明日|明\(\d+\)日).{0,10}?首班車', text):
            tomorrow = ref_date + timedelta(days=1)
            return tomorrow.replace(hour=5, minute=30, second=0, microsecond=0)
        if re.search(r'今日.{0,10}?首班車', text):
            return ref_date.replace(hour=5, minute=30, second=0, microsecond=0)

        # M月D日首班車 - extract specific date for first train
        # Allow weekday markers like "(一)", "(二)" between "日" and "首班車"
        first_train_pattern = r'(\d{1,2})月(\d{1,2})日(?:\([一二三四五六日]\))?.{0,10}?首班車'
        match = re.search(first_train_pattern, text)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            year = ref_date.year
            try:
                result = datetime(year, month, day, 5, 30, tzinfo=TAIPEI_TZ)
                if result >= ref_date:  # Only if date is today or future
                    return result
            except ValueError:
                pass

        # Pattern 2.6: 明日末班車 or 今日末班車 (last train, assume 11:30 PM)
        if re.search(r'(?:明日|明\(\d+\)日).{0,10}?末班車', text):
            tomorrow = ref_date + timedelta(days=1)
            return tomorrow.replace(hour=23, minute=30, second=0, microsecond=0)
        if re.search(r'今日.{0,10}?末班車', text):
            return ref_date.replace(hour=23, minute=30, second=0, microsecond=0)

        # Pattern 2.7: "X時前停駛" means "X時恢復"
        # "今日18時前停駛" → "今日18時恢復"
        # "明日10點前停駛" → "明日10點恢復"
        # IMPORTANT: Ensure no "後" between "前" and "停駛" (avoid "12時前...12時後停駛")
        stop_before_pattern = r'(\d{1,2})[時點]前([^後]{0,50}?)(?:停駛|不通)'
        match = re.search(stop_before_pattern, text)
        if match:
            hour = int(match.group(1))
            # Check if it's today or tomorrow (look at wider context)
            context = text[max(0, match.start()-50):match.start()]
            if re.search(r'明(?:\(\d+\))?日', context):
                tomorrow = ref_date + timedelta(days=1)
                return tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
            else:
                return ref_date.replace(hour=hour, minute=0, second=0, microsecond=0)

        # Pattern 3: M月D日 HH時 with context (must have keywords nearby)
        # Only extract if date appears near resumption keywords
        # Allow time descriptors like "凌晨", "上午", "下午" between "日" and "時"
        resumption_keywords_p3 = ['預計', '恢復', '復駛', '通車', '修復完成', '營運']
        for keyword in resumption_keywords_p3:
            # Look for date within 30 characters after resumption keyword
            # Allow descriptors like "凌晨", "上午", "下午", "首班車" between "日" and time
            pattern3 = rf'{keyword}.{{0,30}}?(\d{{1,2}})月(\d{{1,2}})日(?:[凌上下午首末班車\s]{{0,10}})?(\d{{1,2}})[時:](\d{{2}})?'
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

        # Pattern 4: 今日恢復 (without specific time) - must have resumption keywords
        # IMPORTANT: Exclude uncertain resumptions (陸續, 俟, 待, 視...而定)
        if '今日' in text and not re.search(pattern1, text):
            # Check for uncertainty indicators
            uncertainty_keywords = ['陸續', '俟', '待.*?確認', '視.*?而定', '機動', '暫定']
            has_uncertainty = any(re.search(pattern, text) for pattern in uncertainty_keywords)

            if not has_uncertainty:
                # Only use fallback if there are clear resumption indicators
                if any(kw in text for kw in ['恢復通車', '恢復行駛', '恢復營運']):
                    return ref_date.replace(hour=23, minute=59, second=59, microsecond=0)

        # Pattern 5: 明日恢復 (without specific time) - must have resumption keywords
        # IMPORTANT: Exclude uncertain resumptions
        if re.search(r'明(?:\(\d+\))?日', text) and not re.search(pattern2, text):
            # Check if it's about first/last train (already handled above)
            if not re.search(r'(?:首|末)班車', text):
                # Check for uncertainty indicators
                uncertainty_keywords = ['陸續', '俟', '待.*?確認', '視.*?而定', '機動', '暫定']
                has_uncertainty = any(re.search(pattern, text) for pattern in uncertainty_keywords)

                if not has_uncertainty:
                    # Only use fallback if there are clear resumption indicators
                    if any(kw in text for kw in ['恢復通車', '恢復行駛', '恢復營運']):
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
        # IMPORTANT: Exclude train schedule, incident time, suspension time, etc.
        # IMPORTANT: Simple keywords FIRST to avoid greedy compound matching
        resumption_keywords = [
            '預計', '搶通', '修復完成', '恢復', '復駛', '通車', '營運',  # Simple keywords (priority)
            '預計.{0,20}?恢復', '預計.{0,20}?復駛', '預計.{0,20}?通車', '預計.{0,20}?搶通',  # Compound (limited length)
        ]
        for keyword in resumption_keywords:
            # Look for time within 10 characters after resumption keyword (stricter than before)
            pattern = rf'{keyword}.{{0,10}}?(\d{{1,2}})[：:時](\d{{2}})'
            match = re.search(pattern, text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))

                # Get context around the match (20 chars before and after)
                context_start = max(0, match.start()-20)
                context_end = min(len(text), match.end()+20)
                context = text[context_start:context_end]

                # Exclusion checks
                exclusion_patterns = [
                    r'次\s*[\(（].*?[=開]',  # Train schedule: "306次(花蓮06:24="
                    r'[成發]立',  # Establishment: "成立應變小組"
                    r'應變',  # Emergency response: "應變小組"
                    r'接駁',  # Shuttle: "接駁車"
                    r'發車',  # Departure: "發車時刻"
                    r'開車',  # Departure: "開車時刻"
                    r'發布',  # Announcement time: "14時發布新聞稿"
                    r'到.{0,5}站',  # Arrival: "22:31到新左營站"
                    r'開.{0,5}站',  # Departure: "8:00開台北站"
                ]

                # Check if context contains exclusion patterns
                skip = False
                for excl_pattern in exclusion_patterns:
                    if re.search(excl_pattern, context):
                        logger.debug(f"Skipping time {hour}:{minute} due to exclusion pattern: {excl_pattern}")
                        skip = True
                        break

                if skip:
                    continue

                return ref_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        logger.debug(f"No resumption time pattern matched in text: {text[:100]}...")
        return None

    except Exception as e:
        logger.debug(f"Error parsing resumption time from '{text[:100]}...': {e}")
        return None
