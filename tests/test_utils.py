"""
Unit tests for utility functions
"""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from src.utils.hash_utils import compute_hash
from src.utils.date_utils import parse_tra_date, parse_resumption_time
from src.scrapers.list_scraper import normalize_publish_date
from src.scrapers.detail_scraper import is_rejected_response


class TestHashUtils:
    """Tests for hash computation"""

    def test_compute_hash_consistency(self):
        """Test that same input produces same hash"""
        html = "<html><body>測試內容</body></html>"
        hash1 = compute_hash(html)
        hash2 = compute_hash(html)
        assert hash1 == hash2

    def test_compute_hash_format(self):
        """Test hash format is md5:hexdigest"""
        html = "test"
        result = compute_hash(html)
        assert result.startswith("md5:")
        assert len(result) == 36  # "md5:" + 32 hex characters

    def test_compute_hash_chinese_characters(self):
        """Test hash handles Chinese characters correctly"""
        html = "臺灣鐵路管理局最新消息"
        result = compute_hash(html)
        assert result.startswith("md5:")
        # Should not raise encoding errors


class TestDateUtils:
    """Tests for date parsing"""

    def test_parse_tra_date(self):
        """Test TRA date format parsing"""
        assert parse_tra_date("2025/10/21") == "2025-10-21"
        assert parse_tra_date("2025/01/01") == "2025-01-01"

    def test_parse_resumption_time_today(self):
        """Test parsing 'today' time expressions"""
        result = parse_resumption_time("預計於今日19:00恢復行駛", "2025/08/13")
        assert result is not None
        assert result.hour == 19
        assert result.minute == 0
        assert result.tzinfo == ZoneInfo("Asia/Taipei")

    def test_parse_resumption_time_month_day(self):
        """Test parsing month/day expressions"""
        result = parse_resumption_time("預計8月13日12時前恢復", "2025/08/12")
        assert result is not None
        assert result.month == 8
        assert result.day == 13
        assert result.hour == 12

    def test_parse_resumption_time_none_on_failure(self):
        """Test returns None for invalid input"""
        assert parse_resumption_time("無效文字", "2025/08/13") is None
        assert parse_resumption_time("", "2025/08/13") is None


class TestListScraperUtils:
    """Tests for list scraper helpers"""

    def test_normalize_publish_date_requires_date_cell(self):
        assert normalize_publish_date("2026/2/5") == "2026/02/05"
        assert normalize_publish_date("2026/02/05") == "2026/02/05"
        assert normalize_publish_date("活動 2/7-2/8 臺北車站") == ""


class TestDetailScraperUtils:
    """Tests for detail scraper helpers"""

    def test_detects_rejected_response(self):
        assert is_rejected_response(
            "Request Rejected The requested URL was rejected. Please consult with your administrator."
        )
        assert not is_rejected_response("臺鐵公司列車恢復正常行駛")
