"""
综合测试：验证数据完整性修复

测试范围：
1. Announcement模型序列化不丢失时间字段
2. JSONStorage保存后数据完整性验证
3. 数据恢复成功
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import json
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

from src.models.announcement import Announcement, Classification, VersionEntry
from src.storage.json_storage import JSONStorage


class TestAnnouncementModelFix:
    """测试Announcement模型字段不丢失"""

    def test_model_has_time_fields(self):
        """测试模型定义包含时间字段"""
        from src.models.announcement import Announcement

        # Check model fields (keys are the field names in Pydantic v2)
        fields = set(Announcement.model_fields.keys())

        assert 'predicted_resumption_time' in fields, "Model missing predicted_resumption_time field"
        assert 'actual_resumption_time' in fields, "Model missing actual_resumption_time field"

        print("✓ Model has time fields defined")

    def test_model_serialization_preserves_time_fields(self):
        """测试模型序列化保留时间字段"""
        taipei_tz = ZoneInfo("Asia/Taipei")

        # Create announcement with time data
        announcement = Announcement(
            id="test123",
            title="Test Announcement",
            publish_date="2025/10/22",
            detail_url="http://test.com",
            classification=Classification(
                category="Disruption_Resumption",
                keywords=["test"],
                event_group_id="20251022_Test"
            ),
            version_history=[],
            predicted_resumption_time=datetime(2025, 10, 22, 12, 0, tzinfo=taipei_tz),
            actual_resumption_time=datetime(2025, 10, 22, 14, 0, tzinfo=taipei_tz)
        )

        # Serialize
        serialized = announcement.model_dump(mode='json')

        # Verify time fields are present
        assert 'predicted_resumption_time' in serialized
        assert 'actual_resumption_time' in serialized
        assert serialized['predicted_resumption_time'] is not None
        assert serialized['actual_resumption_time'] is not None

        print("✓ Model serialization preserves time fields")

    def test_model_with_none_time_fields(self):
        """测试None值的时间字段也能正确序列化"""
        announcement = Announcement(
            id="test456",
            title="Test Announcement 2",
            publish_date="2025/10/22",
            detail_url="http://test.com",
            classification=Classification(
                category="General_Operation",
                keywords=[],
                event_group_id="20251022_Test2"
            ),
            version_history=[],
            predicted_resumption_time=None,
            actual_resumption_time=None
        )

        serialized = announcement.model_dump(mode='json')

        # Fields should exist even if None
        assert 'predicted_resumption_time' in serialized
        assert 'actual_resumption_time' in serialized

        print("✓ Model handles None time fields correctly")


class TestJSONStorageIntegrity:
    """测试JSONStorage数据完整性"""

    def test_save_and_load_preserves_time_data(self):
        """测试保存和加载保留时间数据"""
        taipei_tz = ZoneInfo("Asia/Taipei")

        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            storage = JSONStorage(output_file=temp_file)

            # Create test data with time fields
            announcements = [
                Announcement(
                    id="test1",
                    title="Test 1",
                    publish_date="2025/10/22",
                    detail_url="http://test.com/1",
                    classification=Classification(
                        category="Disruption_Resumption",
                        keywords=["test"],
                        event_group_id="20251022_Test1"
                    ),
                    version_history=[],
                    predicted_resumption_time=datetime(2025, 10, 22, 12, 0, tzinfo=taipei_tz),
                    actual_resumption_time=None
                ),
                Announcement(
                    id="test2",
                    title="Test 2",
                    publish_date="2025/10/22",
                    detail_url="http://test.com/2",
                    classification=Classification(
                        category="Disruption_Resumption",
                        keywords=["test"],
                        event_group_id="20251022_Test2"
                    ),
                    version_history=[],
                    predicted_resumption_time=None,
                    actual_resumption_time=datetime(2025, 10, 22, 14, 0, tzinfo=taipei_tz)
                )
            ]

            # Save
            storage.save(announcements)

            # Load
            loaded = storage.load()

            # Verify
            assert len(loaded) == 2
            assert loaded[0].predicted_resumption_time is not None
            assert loaded[0].actual_resumption_time is None
            assert loaded[1].predicted_resumption_time is None
            assert loaded[1].actual_resumption_time is not None

            print("✓ JSONStorage preserves time data after save/load cycle")

        finally:
            # Cleanup
            Path(temp_file).unlink(missing_ok=True)
            Path(str(temp_file) + ".lock").unlink(missing_ok=True)

    def test_integrity_validation_detects_data_loss(self):
        """测试数据完整性验证能检测到数据丢失"""
        taipei_tz = ZoneInfo("Asia/Taipei")

        announcements_with_time = [
            Announcement(
                id="test1",
                title="Test 1",
                publish_date="2025/10/22",
                detail_url="http://test.com/1",
                classification=Classification(
                    category="Disruption_Resumption",
                    keywords=["test"],
                    event_group_id="20251022_Test1"
                ),
                version_history=[],
                predicted_resumption_time=datetime(2025, 10, 22, 12, 0, tzinfo=taipei_tz)
            )
        ]

        announcements_without_time = [
            Announcement(
                id="test1",
                title="Test 1",
                publish_date="2025/10/22",
                detail_url="http://test.com/1",
                classification=Classification(
                    category="Disruption_Resumption",
                    keywords=["test"],
                    event_group_id="20251022_Test1"
                ),
                version_history=[],
                predicted_resumption_time=None  # Time data lost!
            )
        ]

        storage = JSONStorage()

        # Should raise ValueError when time data is lost
        with pytest.raises(ValueError, match="TIME FIELD DATA LOSS DETECTED"):
            storage._validate_data_integrity(announcements_with_time, announcements_without_time)

        print("✓ Integrity validation detects time data loss")


class TestDataRecovery:
    """测试数据恢复"""

    def test_master_json_has_time_data(self):
        """测试master.json包含恢复的时间数据"""
        master_file = Path("data/master.json")

        if not master_file.exists():
            pytest.skip("master.json not found")

        with open(master_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Count time extractions
        time_count = sum(
            1 for a in data
            if a.get('predicted_resumption_time') or a.get('actual_resumption_time')
        )

        # Should have 22 time extractions (13 predicted + 9 actual)
        assert time_count == 22, f"Expected 22 time extractions, found {time_count}"

        predicted_count = sum(1 for a in data if a.get('predicted_resumption_time'))
        actual_count = sum(1 for a in data if a.get('actual_resumption_time'))

        assert predicted_count == 13, f"Expected 13 predicted times, found {predicted_count}"
        assert actual_count == 9, f"Expected 9 actual times, found {actual_count}"

        print(f"✓ Data recovery successful: {time_count} time extractions ({predicted_count} predicted + {actual_count} actual)")


def run_all_tests():
    """运行所有测试"""
    print("=" * 80)
    print("数据完整性修复 - 综合测试")
    print("=" * 80)
    print()

    # Test 1: Model fix
    print("【测试1】Announcement模型修复")
    print("-" * 80)
    test_model = TestAnnouncementModelFix()
    test_model.test_model_has_time_fields()
    test_model.test_model_serialization_preserves_time_fields()
    test_model.test_model_with_none_time_fields()
    print()

    # Test 2: Storage integrity
    print("【测试2】JSONStorage完整性验证")
    print("-" * 80)
    test_storage = TestJSONStorageIntegrity()
    test_storage.test_save_and_load_preserves_time_data()
    test_storage.test_integrity_validation_detects_data_loss()
    print()

    # Test 3: Data recovery
    print("【测试3】数据恢复验证")
    print("-" * 80)
    test_recovery = TestDataRecovery()
    test_recovery.test_master_json_has_time_data()
    print()

    print("=" * 80)
    print("✅ 所有测试通过！数据完整性修复成功")
    print("=" * 80)


if __name__ == '__main__':
    run_all_tests()
