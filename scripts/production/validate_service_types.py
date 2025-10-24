#!/usr/bin/env python3
"""
驗證服務類型標記的準確性
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")


def validate_service_types():
    """驗證服務類型分布和準確性"""

    data_file = project_root / "data" / "master.json"

    # Load data
    logger.info(f"加載數據: {data_file}")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"總公告數: {len(data)}")

    # Statistics
    service_type_counts = defaultdict(int)
    service_details_counts = defaultdict(int)

    # Track announcements with service types
    announcements_with_service_type = []

    for ann in data:
        latest_version = ann['version_history'][0]
        extracted = latest_version['extracted_data']

        service_type = extracted.get('service_type')
        service_details = extracted.get('service_details')

        if service_type:
            service_type_counts[service_type] += 1
            announcements_with_service_type.append({
                'title': ann['title'],
                'service_type': service_type,
                'service_details': service_details,
                'actual_time': extracted.get('actual_resumption_time')
            })

        if service_details:
            service_details_counts[service_details] += 1

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("服務類型分布統計")
    logger.info("=" * 80)

    logger.info(f"\n總公告數: {len(data)}")
    logger.info(f"有服務類型標記的公告數: {len(announcements_with_service_type)}")
    logger.info(f"有實際恢復時間的公告數: {sum(1 for ann in data if ann['version_history'][0]['extracted_data'].get('actual_resumption_time'))}")

    logger.info("\n服務類型分布:")
    for service_type, count in sorted(service_type_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {service_type}: {count}")

    logger.info("\n服務詳情分布:")
    for details, count in sorted(service_details_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {details}: {count}")

    # Detailed list
    logger.info("\n" + "=" * 80)
    logger.info("詳細列表（有服務類型標記的公告）")
    logger.info("=" * 80)

    # Group by service type
    for service_type in ['shuttle_service', 'partial_operation', 'normal_train']:
        anns_of_type = [a for a in announcements_with_service_type if a['service_type'] == service_type]
        if anns_of_type:
            logger.info(f"\n【{service_type}】({len(anns_of_type)} 個):")
            for ann in anns_of_type:
                logger.info(f"  - {ann['title'][:60]}")
                if ann['service_details']:
                    logger.info(f"    詳情: {ann['service_details']}")
                if ann['actual_time']:
                    logger.info(f"    時間: {ann['actual_time']}")

    logger.info("\n" + "=" * 80)

    return service_type_counts


if __name__ == "__main__":
    counts = validate_service_types()
    logger.success(f"✅ 驗證完成！")
