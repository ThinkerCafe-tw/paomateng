#!/usr/bin/env python3
"""
Test the 10 problematic samples after fixes
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.date_utils import parse_resumption_time
from datetime import datetime
from zoneinfo import ZoneInfo


def test_samples():
    """Test the 10 samples that had issues"""

    test_cases = [
        {
            "id": "Sample 2",
            "title": "臺鐵公司康樂=臺東間電車線設備受損搶修及列車行駛資訊 第1發",
            "publish_date": "2025/04/12",
            "text": "發生時間：114年4月12日16時05分。",
            "expected": None,  # Should NOT extract incident time
            "old_wrong": "2025-04-12T16:05:00+08:00"
        },
        {
            "id": "Sample 4",
            "title": "平溪線因豪雨暫停營運　臺鐵持續監測確保行車安全",
            "publish_date": "2025/10/21",
            "text": "瑞芳站發車時刻為08:30、10:30、14:00及16:00",
            "expected": None,  # Should NOT extract shuttle departure time
            "old_wrong": "2025-10-21T08:30:00+08:00"
        },
        {
            "id": "Sample 5",
            "title": "受強降雨影響北迴線和仁至崇德間鐵路預計於5月21日搶通東正線恢復單線雙向行車 第11發",
            "publish_date": "2025/05/20",
            "text": "預計5月21日凌晨4：00完成。經號誌通訊系統驗測後，進行試運轉，預計5月21日首班車恢復東正線正常通行",
            "expected": "2025-05-21T05:30:00+08:00",  # Should extract 5/21 first train
            "old_wrong": "2025-05-20T05:00:00+08:00"
        },
        {
            "id": "Sample 6",
            "title": "臺鐵公司因應天兔颱風列車行駛資訊 第1發",
            "publish_date": "2024/11/14",
            "text": "配合天兔颱風陸上颱風警報發布，本公司已於17時30分成立一級應變小組",
            "expected": None,  # Should NOT extract emergency response establishment time
            "old_wrong": "2024-11-14T17:30:00+08:00"
        },
        {
            "id": "Sample 8",
            "title": "臺鐵公司因應康芮颱風列車行駛資訊 第4發",
            "publish_date": "2024/10/31",
            "text": "基隆=彰化間12時前視風雨狀況機動行駛，12時後全面停駛",
            "expected": None,  # Should NOT extract suspension time (but 12時前停駛 might match Pattern 2.7)
            "old_wrong": "2024-10-31T12:00:00+08:00",
            "note": "Pattern 2.7 might extract 12:00 as resumption time - check if this is appropriate"
        },
        {
            "id": "Sample 9",
            "title": "強降雨致北迴線雙向中斷路線受損搶修概況及旅客疏運應變措施 第3發",
            "publish_date": "2025/05/19",
            "text": "發生時間：114年5月18日16時10分",
            "expected": None,  # Should NOT extract incident time
            "old_wrong": "2025-05-19T05:30:00+08:00"
        },
        {
            "id": "Sample 10",
            "title": "強降雨影響北迴線路線受損搶修復原及旅客疏運最新概況 第6發",
            "publish_date": "2025/05/19",
            "text": "發生時間：114年5月18日16時10分。預估5月21日(三)首班車恢復東正線單線雙向行車",
            "expected": "2025-05-21T05:30:00+08:00",  # Should extract 5/21 first train, NOT incident time
            "old_wrong": "2025-05-19T20:00:00+08:00"
        },
    ]

    print("=" * 100)
    print("Testing Fixed Samples")
    print("=" * 100)

    passed = 0
    failed = 0
    warnings = 0

    for tc in test_cases:
        result = parse_resumption_time(tc["text"], tc["publish_date"])

        # Convert expected string to datetime for comparison
        expected = None
        if tc["expected"]:
            expected = datetime.fromisoformat(tc["expected"])

        # Compare datetime objects, not strings
        matches = (result == expected)

        result_str = str(result) if result else "None"
        expected_str = tc["expected"] if tc["expected"] else "None"

        status = "✅ PASS" if matches else "❌ FAIL"

        if not matches:
            failed += 1
        else:
            passed += 1

        print(f"\n{tc['id']}: {status}")
        print(f"  Publish: {tc['publish_date']}")
        print(f"  Text: {tc['text'][:80]}...")
        print(f"  Expected: {expected_str}")
        print(f"  Got:      {result_str}")
        if result_str != expected_str:
            print(f"  Old Wrong: {tc.get('old_wrong', 'N/A')}")
        if tc.get('note'):
            print(f"  ⚠️  Note: {tc['note']}")
            warnings += 1

    print("\n" + "=" * 100)
    print(f"Results: {passed} passed, {failed} failed, {warnings} warnings")
    print("=" * 100)

    return failed == 0


if __name__ == "__main__":
    success = test_samples()
    sys.exit(0 if success else 1)
