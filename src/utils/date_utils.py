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
        # IMPORTANT: Only remove the date/time portion, not the entire sentence
        # Pattern: "發佈日期：2025/7/8 下午 4:55" (date + optional time period + time)
        text = re.sub(r'發[佈布]日期[：:]\s*\d{4}[/\-年]\d{1,2}[/\-月]\d{1,2}日?(?:\s*[上下]午)?\s*\d{1,2}[：:]\d{2}', '', text)

        # Remove "發生時間" section to avoid extracting incident time as resumption time
        # IMPORTANT: Only remove the time portion, not the entire sentence
        text = re.sub(r'發生時間[：:]\s*\d{4}[/\-年]\d{1,2}[/\-月]\d{1,2}日?(?:\s*[上下]午)?\s*\d{1,2}[：:]\d{2}', '', text)

        # Pattern 0: Explicit "預計X時" or "預估X時" (PRIORITY pattern for predicted times)
        # This must be checked FIRST to prioritize explicit predictions over actual times
        # Handles "預計18時" (no minutes) and "預計18:30" (with minutes)
        # Example: "已於16:48恢復單線，預計18時恢復雙線" → should extract 18:00, not 16:48
        # IMPORTANT: Skip if text contains "首班車恢復" (first train has higher semantic priority)
        # Example: "預估5：00搶通...預計5月21日首班車恢復" → should extract first train (05:30), not repair time (05:00)
        prediction_pattern = r'預[計估][\s]?(\d{1,2})[：:時](\d{2})?'
        match = re.search(prediction_pattern, text)
        if match:
            # Check context after the match for exclusions
            context_after = text[match.end():min(len(text), match.end()+50)]

            # Exclusion 1: Train arrival times - "預計22:31(...次)到...站"
            # Example: "預計22:31(432次)、23:45(442次)到新左營站"
            if re.search(r'\([^)]*次\).*?到.*?站', context_after):
                logger.debug(f"Skipping Pattern 0 (預計X時): train arrival time, not resumption")
            # Exclusion 2: First train resumption (higher priority for passenger service)
            elif re.search(r'首班車.*?恢復', text) or re.search(r'恢復.*?首班車', text):
                logger.debug(f"Skipping Pattern 0 (預計X時): text contains first train resumption (higher priority)")
                # Let Pattern 2.5 handle first train time extraction
            else:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0

                # Special handling for 24時 (midnight) → convert to next day 00:00
                if hour == 24:
                    tomorrow = ref_date + timedelta(days=1)
                    return tomorrow.replace(hour=0, minute=minute, second=0, microsecond=0)
                else:
                    return ref_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Pattern 1: 今日/本日 HH:MM or 今日/本日HH:MM
        # IMPORTANT: Exclude announcement publication times ("發布新聞稿") and other non-resumption contexts
        pattern1 = r'[今本]日\s*(\d{1,2})[：:時](\d{2})?'
        match = re.search(pattern1, text)
        if match:
            # Check context after the match for exclusion patterns (within 20 chars)
            context_after = text[match.end():min(len(text), match.end()+20)]
            # NEW: Added '後停駛' to prevent extracting typhoon suspension start times
            # Example: "今日12時後停駛" = suspension starts at 12:00, NOT resumption
            exclusion_keywords = ['發布', '發車', '開車', '到站', '成立', '應變', '後停駛']

            if any(kw in context_after for kw in exclusion_keywords):
                logger.debug(f"Skipping Pattern 1 (今日HH:MM) due to exclusion keyword in context: {context_after[:20]}")
                # This is not a resumption time - skip to next pattern
            else:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0

                # Special handling for 24時 (midnight) → convert to next day 00:00
                if hour == 24:
                    tomorrow = ref_date + timedelta(days=1)
                    return tomorrow.replace(hour=0, minute=minute, second=0, microsecond=0)
                else:
                    return ref_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Pattern 1.5: 今(X)日 HH:MM - "今(8)日18時" means use day=8 (NOT ref_date)
        pattern1_5 = r'今\((\d+)\)日\s*(\d{1,2})[：:時](\d{2})?'
        match = re.search(pattern1_5, text)
        if match:
            # Check context for exclusion (extended to 50 chars to catch "01:00完成...試運轉")
            context_after = text[match.end():min(len(text), match.end()+50)]
            # IMPORTANT: Exclude suspension times like "今(22)日15時後停駛"
            # IMPORTANT: Exclude test operations like "今(19)日01:00完成...試運轉"
            exclusion_keywords = ['發布', '發車', '開車', '到站', '成立', '應變', '停駛', '後', '前', '試運轉', '完成試車']

            if any(kw in context_after for kw in exclusion_keywords):
                logger.debug(f"Skipping Pattern 1.5 (今(X)日HH:MM) due to exclusion keyword")
            else:
                day = int(match.group(1))
                hour = int(match.group(2))
                minute = int(match.group(3)) if match.group(3) else 0
                try:
                    return ref_date.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
                except ValueError:
                    pass  # Invalid date, fall through

        # Pattern 2: 明日 HH:MM or 明日HH:MM or 明(X)日HH:MM
        # For "明(X)日", use X as the day (NOT ref_date + 1)
        # IMPORTANT: Skip if this is "X時前停駛" pattern (handled by Pattern 2.7)
        pattern2 = r'明(?:\((\d+)\))?日\s*(\d{1,2})[：:時](\d{2})?'
        match = re.search(pattern2, text)
        if match:
            # Check if this is a non-resumption context
            # Look ahead after the match (15 chars) for exclusion patterns
            check_pos = match.end()
            remaining = text[check_pos:check_pos+15]

            # Exclusion patterns:
            # - "前停駛/不通" → Pattern 2.7
            # - "前之/前的" → describing information, not resumption
            # - "資訊/發布" → announcement info, not resumption
            exclusions = ['前停駛', '前不通', '前之', '前的', '資訊', '發布']

            if any(excl in remaining for excl in exclusions):
                # This is not "明日X時恢復" - skip this match
                logger.debug(f"Skipping Pattern 2 due to exclusion in context: {remaining[:15]}")
                pass
            else:
                paren_day = match.group(1)  # Day in parentheses (if exists)
                hour = int(match.group(2))
                minute = int(match.group(3)) if match.group(3) else 0

                if paren_day:
                    # "明(X)日" format - use X as the day
                    day = int(paren_day)
                    try:
                        result = ref_date.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
                        return result
                    except ValueError:
                        pass  # Invalid date, fall through to default tomorrow

                # Regular "明日" - add 1 day
                tomorrow = ref_date + timedelta(days=1)
                return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Pattern 2.5: 明日首班車 or 今日首班車 or M月D日首班車 (first train, assume 5:30 AM)
        # For "明(X)日首班車", use X as the day (NOT ref_date + 1)
        tomorrow_first_train = re.search(r'明(?:\((\d+)\))?日.{0,10}?首班車', text)
        if tomorrow_first_train:
            paren_day = tomorrow_first_train.group(1)
            if paren_day:
                # "明(X)日首班車" - use X as the day
                day = int(paren_day)
                try:
                    result = ref_date.replace(day=day, hour=5, minute=30, second=0, microsecond=0)
                    return result
                except ValueError:
                    pass  # Invalid date, fall through
            # Regular "明日首班車" - add 1 day
            tomorrow = ref_date + timedelta(days=1)
            return tomorrow.replace(hour=5, minute=30, second=0, microsecond=0)

        if re.search(r'今日.{0,10}?首班車', text):
            # IMPORTANT: Exclude shuttle service times like "今日首班車起...接駁服務"
            match = re.search(r'今日.{0,10}?首班車', text)
            if match:
                context_after = text[match.end():min(len(text), match.end()+30)]
                if '接駁' not in context_after:
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
        # For "明(X)日末班車", use X as the day (NOT ref_date + 1)
        tomorrow_last_train = re.search(r'明(?:\((\d+)\))?日.{0,10}?末班車', text)
        if tomorrow_last_train:
            paren_day = tomorrow_last_train.group(1)
            if paren_day:
                # "明(X)日末班車" - use X as the day
                day = int(paren_day)
                try:
                    result = ref_date.replace(day=day, hour=23, minute=30, second=0, microsecond=0)
                    return result
                except ValueError:
                    pass  # Invalid date, fall through
            # Regular "明日末班車" - add 1 day
            tomorrow = ref_date + timedelta(days=1)
            return tomorrow.replace(hour=23, minute=30, second=0, microsecond=0)

        if re.search(r'今日.{0,10}?末班車', text):
            return ref_date.replace(hour=23, minute=30, second=0, microsecond=0)

        # Pattern 2.65: "X月X日至X月X日暫停/停駛" - date range suspension
        # "10月23日至10月25日暫停行駛" → resumption after 10/25 (assume end of day 23:59)
        # Extract the END date as resumption time
        date_range_pattern = r'(\d{1,2})月(\d{1,2})日至(\d{1,2})月(\d{1,2})日.{0,20}?(?:暫停|停駛|停運|不通)'
        match = re.search(date_range_pattern, text)
        if match:
            # End date is the resumption point
            end_month = int(match.group(3))
            end_day = int(match.group(4))
            year = ref_date.year
            try:
                # Resumption is at end of the last suspension day (23:59)
                result = datetime(year, end_month, end_day, 23, 59, tzinfo=TAIPEI_TZ)
                if result >= ref_date:  # Only if date is today or future
                    return result
            except ValueError:
                logger.debug(f"Invalid date range: {year}/{end_month}/{end_day}")
                pass  # Fall through to other patterns

        # Pattern 2.7: "X時前停駛" means "X時恢復" (with uncertainty checks)
        # "今日18時前停駛" → "今日18時恢復"
        # "明日10點前停駛" → "明日10點恢復"
        # "16日12時前停駛" → "16日12時恢復"
        # "明(23)日12時前停駛" → "23日12時恢復" (use date in parentheses, NOT +1 day)
        # IMPORTANT: Ensure no "後" between "前" and "停駛" (avoid "12時前...12時後停駛")
        # IMPORTANT: Skip if resumption is CONDITIONAL/UNCERTAIN (俟...後, 陸續, 視...而定)
        # SPECIAL: Handle "24時" as next day 00:00
        stop_before_pattern = r'(\d{1,2})[時點]前([^後]{0,50}?)(?:停駛|不通)'
        match = re.search(stop_before_pattern, text)
        if match:
            # Check for uncertainty/conditionality in the text (within 100 chars after match)
            context_after_match = text[match.end():min(len(text), match.end()+100)]
            uncertainty_patterns = [
                r'俟.*?後',  # "俟颱風離境後" = wait until... (uncertain timing)
                r'陸續.*?恢復',  # "陸續恢復" = gradual resumption (uncertain)
                r'視.*?而定',  # "視...而定" = depends on... (uncertain)
                r'待.*?確認',  # "待確認後" = after confirmation (uncertain)
            ]

            if any(re.search(pattern, context_after_match) for pattern in uncertainty_patterns):
                logger.debug(f"Skipping Pattern 2.7 (X時前停駛): resumption is conditional/uncertain")
            else:
                hour = int(match.group(1))

                # Special handling for 24時 (midnight) → convert to next day 00:00
                if hour == 24:
                    hour = 0
                    add_one_day = True
                else:
                    add_one_day = False

                # Check wider context (100 chars before match for date indicators)
                context = text[max(0, match.start()-100):match.start()]

                # Priority 1: "明(X)日" format - use X as the day (NOT ref_date + 1)
                paren_date = re.search(r'明\((\d{1,2})\)日', context)
                if paren_date:
                    day = int(paren_date.group(1))
                    try:
                        result = ref_date.replace(day=day, hour=hour, minute=0, second=0, microsecond=0)
                        if add_one_day:
                            result = result + timedelta(days=1)
                        return result
                    except ValueError:
                        pass  # Invalid date, fall through

                # Priority 2: Explicit "X日" (e.g., "16日12時前") - use X as the day
                # Must NOT be part of "今日" or "明日"
                explicit_day = re.search(r'(?<!今)(?<!明)(\d{1,2})日', context)
                if explicit_day:
                    day = int(explicit_day.group(1))
                    try:
                        result = ref_date.replace(day=day, hour=hour, minute=0, second=0, microsecond=0)
                        if add_one_day:
                            result = result + timedelta(days=1)
                        if result >= ref_date:  # Only if date is today or future
                            return result
                    except ValueError:
                        pass  # Invalid date, fall through

                # Priority 3: "明日" (without parentheses) - add 1 day
                if re.search(r'明日', context) and not paren_date:
                    tomorrow = ref_date + timedelta(days=1)
                    result = tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
                    if add_one_day:
                        result = result + timedelta(days=1)
                    return result

                # Priority 4: Default to today
                result = ref_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                if add_one_day:
                    result = result + timedelta(days=1)
                return result

        # Pattern 2.8: DELETED
        # "X時後停駛" is suspension START time, NOT resumption time
        # Should NOT be extracted as resumption time
        # Example: "15時後南迴線停駛" means "suspension starts at 15:00", NOT "resumes at 15:00"

        # Pattern 2.9: "X時以前/以後" with suspension context
        # "12時以前停駛" → resumption at 12:00
        # IMPORTANT: "12時以前正常行駛" → NOT a resumption time (means suspension starts AFTER 12:00)
        before_after_pattern = r'(\d{1,2})[時點]以[前後].*?(?:停駛|不通|正常)'
        match = re.search(before_after_pattern, text)
        if match:
            matched_text = match.group(0)

            # CRITICAL: Skip if "正常" is the ending (means normal BEFORE time, not resumption)
            # "X時以前正常" = normal until X, NOT resumption at X
            if '正常' in matched_text and not ('停駛' in matched_text or '不通' in matched_text):
                logger.debug(f"Skipping Pattern 2.9 due to '以前正常' (not resumption): {matched_text}")
            else:
                # This is a valid resumption pattern (以前停駛 = resumption at X)
                hour = int(match.group(1))
                context = text[max(0, match.start()-100):match.start()]

                # Check for date context
                paren_date = re.search(r'明\((\d{1,2})\)日', context)
                if paren_date:
                    day = int(paren_date.group(1))
                    try:
                        return ref_date.replace(day=day, hour=hour, minute=0, second=0, microsecond=0)
                    except ValueError:
                        pass

                explicit_day = re.search(r'(?<!今)(?<!明)(\d{1,2})日', context)
                if explicit_day:
                    day = int(explicit_day.group(1))
                    try:
                        result = ref_date.replace(day=day, hour=hour, minute=0, second=0, microsecond=0)
                        if result >= ref_date:
                            return result
                    except ValueError:
                        pass

                if re.search(r'明日', context) and not paren_date:
                    tomorrow = ref_date + timedelta(days=1)
                    return tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)

                return ref_date.replace(hour=hour, minute=0, second=0, microsecond=0)

        # Pattern 2.10: "恢復通車" or "恢復雙向通車" with time
        # Example: "西正線於16:50先行恢復單線雙向通車，17:00恢復雙向通車"
        # Priority: EARLIEST resumption time (16:50), not full recovery (17:00)
        # Rationale: Actual resumption = when service first becomes available to passengers
        # Look for time before or after "恢復.*通車"

        recovery_patterns = [
            (r'(?:於|預計)?[\s]?(\d{1,2})[：:時](\d{2})?.{0,10}?恢復(?:單線)?(?:雙向)?通車', 'forward'),  # Time before "恢復通車" (added 單線 to catch partial recovery)
            (r'恢復(?:單線)?(?:雙向)?通車.{0,10}?(\d{1,2})[：:時](\d{2})?', 'backward'),  # Time after "恢復通車"
        ]

        earliest_time = None

        for pattern, direction in recovery_patterns:
            for match in re.finditer(pattern, text):
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0

                # Check if this is "接駁" completion (not resumption)
                context = text[max(0, match.start()-20):min(len(text), match.end()+20)]
                if re.search(r'接駁', context):
                    continue

                # For actual resumption, prefer EARLIEST time (when service first resumes)
                current_time = (hour, minute)
                if earliest_time is None or current_time < earliest_time:
                    earliest_time = current_time

        if earliest_time:
            hour, minute = earliest_time
            # Special handling for 24時 (midnight) → convert to next day 00:00
            if hour == 24:
                tomorrow = ref_date + timedelta(days=1)
                return tomorrow.replace(hour=0, minute=minute, second=0, microsecond=0)
            else:
                return ref_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Pattern 2.11: "預估至X時止" - estimated end time
        # Example: "預估至19時止" means suspension until 19:00
        # This is a resumption time (when the suspension ends)
        estimated_until_pattern = r'預估至[\s]?(\d{1,2})[時點]止'
        match = re.search(estimated_until_pattern, text)
        if match:
            hour = int(match.group(1))

            # Check context to ensure it's about suspension/operations, not unrelated time
            context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
            # Include "接駁" as it often appears with service suspensions
            suspension_keywords = ['中斷', '不通', '停駛', '影響', '搶修', '接駁', '行駛']

            if any(kw in context for kw in suspension_keywords):
                # Special handling for 24時 (midnight)
                if hour == 24:
                    tomorrow = ref_date + timedelta(days=1)
                    return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    return ref_date.replace(hour=hour, minute=0, second=0, microsecond=0)

        # Pattern 3: M月D日 HH時 with context (must have keywords nearby)
        # Only extract if date appears near resumption keywords
        # Allow time descriptors like "凌晨", "上午", "下午" between "日" and "時"
        # IMPORTANT: Exclude incident times (發生, 地震, 淹水) that are NOT resumption times
        resumption_keywords_p3 = ['預計', '恢復', '復駛', '通車', '修復完成', '營運']
        for keyword in resumption_keywords_p3:
            # Look for date within 30 characters after resumption keyword
            # Allow descriptors like "凌晨", "上午", "下午", "首班車" between "日" and time
            pattern3 = rf'{keyword}.{{0,30}}?(\d{{1,2}})月(\d{{1,2}})日(?:[凌上下午首末班車\s]{{0,10}})?(\d{{1,2}})[時:](\d{{2}})?'
            match = re.search(pattern3, text)
            if match:
                # Check context after the time match (within 20 chars) for exclusion keywords
                context_after = text[match.end():min(len(text), match.end()+20)]
                exclusion_keywords = ['發生', '地震', '影響', '淹水', '坍方', '中斷']

                if any(kw in context_after for kw in exclusion_keywords):
                    logger.debug(f"Skipping Pattern 3 (M月D日HH時) due to exclusion keyword in context: {context_after[:20]}")
                    continue

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
            '預計', '搶通', '修復完成', '搶修完成', '搶修完畢', '恢復', '復駛', '通車', '營運',  # Simple keywords (priority)
            '預計.{0,20}?恢復', '預計.{0,20}?復駛', '預計.{0,20}?通車', '預計.{0,20}?搶通',  # Compound (limited length)
        ]
        for keyword in resumption_keywords:
            # Look for time within 10 characters after resumption keyword (stricter than before)
            # Also try reversed: time before keyword (e.g., "17:10搶修完成")
            forward_pattern = rf'{keyword}.{{0,10}}?(\d{{1,2}})[：:時](\d{{2}})'
            backward_pattern = rf'(\d{{1,2}})[：:時](\d{{2}}).{{0,10}}?{keyword}'

            match = re.search(forward_pattern, text)
            if not match:
                match = re.search(backward_pattern, text)

            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))

                # Get context around the match for exclusion checking
                # Short context (30 chars) for proximity-sensitive exclusions (increased from 10 to catch "01:00完成...試運轉")
                # Long context (50 chars) for general exclusions
                short_context_start = max(0, match.start()-30)
                short_context_end = min(len(text), match.end()+30)
                short_context = text[short_context_start:short_context_end]

                long_context_start = max(0, match.start()-50)
                long_context_end = min(len(text), match.end()+50)
                long_context = text[long_context_start:long_context_end]

                # Exclusion checks
                # IMPORTANT: Exclude test/operation times that are NOT resumption times
                # NOTE: "修復" (repair) times ARE resumption times, so we don't exclude them

                # Proximity-sensitive exclusions (must be within 30 chars of time)
                proximity_exclusions = [
                    r'接駁',  # Shuttle: "16:19接駁完畢" (only exclude if near time)
                    r'完成試車',  # Test run completion (test ≠ resumption)
                    r'試運轉',  # Test operation (test ≠ resumption): "01:00完成...試運轉"
                    r'完成.*?試運轉',  # Test run completion with text in between: "01:00完成和仁=崇德間東正線試運轉"
                ]

                # General exclusions (can be anywhere in 50-char context)
                general_exclusions = [
                    r'次\s*[\(（].*?[=開]',  # Train schedule: "306次(花蓮06:24="
                    r'[成發]立',  # Establishment: "成立應變小組"
                    r'應變',  # Emergency response: "應變小組"
                    r'發車',  # Departure: "發車時刻"
                    r'開車',  # Departure: "開車時刻"
                    r'發布',  # Announcement time: "14時發布新聞稿"
                    r'到.{0,5}站',  # Arrival: "22:31到新左營站"
                    r'開.{0,5}站',  # Departure: "8:00開台北站"
                    r'時前.*?停駛',  # Typhoon: "12時前列車停駛"
                    r'時後.*?停駛',  # Typhoon: "15時後南迴線停駛"
                    r'停駛.*?時前',  # Typhoon: "各級列車停駛至12時前"
                    r'停駛.*?時後',  # Typhoon: "各級列車停駛至15時後"
                ]

                # Check proximity-sensitive exclusions first
                skip = False
                for excl_pattern in proximity_exclusions:
                    if re.search(excl_pattern, short_context):
                        logger.debug(f"Skipping time {hour}:{minute} due to proximity exclusion: {excl_pattern}")
                        skip = True
                        break

                if not skip:
                    # Check general exclusions
                    for excl_pattern in general_exclusions:
                        if re.search(excl_pattern, long_context):
                            logger.debug(f"Skipping time {hour}:{minute} due to general exclusion: {excl_pattern}")
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
