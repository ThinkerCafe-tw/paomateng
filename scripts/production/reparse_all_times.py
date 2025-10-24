#!/usr/bin/env python3
"""
重新解析所有公告的时间数据
使用最新的 date_utils 代码更新 master.json
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.date_utils import parse_resumption_time
from src.parsers.content_parser import ContentParser
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")


def reparse_all():
    """重新解析所有公告的时间数据"""

    data_file = project_root / "data" / "master.json"

    # Load data
    logger.info(f"加载数据: {data_file}")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"总公告数: {len(data)}")

    # Initialize parser
    parser = ContentParser()

    # Statistics
    updated_count = 0
    changed_count = 0
    error_count = 0

    # Reparse each announcement
    for i, ann in enumerate(data, 1):
        try:
            ann_id = ann['id']
            title = ann['title']
            publish_date = ann['publish_date']

            # Get the latest version
            latest_version = ann['version_history'][0]
            content_html = latest_version['content_html']
            old_extracted = latest_version['extracted_data']

            # Re-parse
            new_extracted = parser.parse(content_html, publish_date, title)

            # Convert datetime to ISO string for JSON
            old_predicted = old_extracted.get('predicted_resumption_time')
            new_predicted = new_extracted.predicted_resumption_time

            if new_predicted:
                new_predicted_str = new_predicted.isoformat()
            else:
                new_predicted_str = None

            # Check if changed
            if old_predicted != new_predicted_str:
                changed_count += 1
                logger.info(f"[{i}/{len(data)}] 变更: {title[:50]}")
                logger.info(f"  旧: {old_predicted}")
                logger.info(f"  新: {new_predicted_str}")

            # Update extracted data
            latest_version['extracted_data']['predicted_resumption_time'] = new_predicted_str

            # Also update actual_resumption_time
            old_actual = old_extracted.get('actual_resumption_time')
            new_actual = new_extracted.actual_resumption_time

            if new_actual:
                new_actual_str = new_actual.isoformat()
            else:
                new_actual_str = None

            if old_actual != new_actual_str:
                logger.info(f"  Actual 变更: {old_actual} -> {new_actual_str}")

            latest_version['extracted_data']['actual_resumption_time'] = new_actual_str

            # NEW: Update service_type and service_details
            latest_version['extracted_data']['service_type'] = new_extracted.service_type
            latest_version['extracted_data']['service_details'] = new_extracted.service_details

            updated_count += 1

            if i % 20 == 0:
                logger.info(f"进度: {i}/{len(data)}")

        except Exception as e:
            error_count += 1
            logger.error(f"错误 [{ann_id}]: {e}")

    # Save updated data
    logger.info(f"\n保存更新数据到: {data_file}")
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Summary
    logger.info(f"\n{'=' * 80}")
    logger.info(f"重新解析完成")
    logger.info(f"{'=' * 80}")
    logger.info(f"总公告数: {len(data)}")
    logger.info(f"已更新: {updated_count}")
    logger.info(f"有变更: {changed_count}")
    logger.info(f"错误数: {error_count}")
    logger.info(f"{'=' * 80}")

    return changed_count, error_count


if __name__ == "__main__":
    changed, errors = reparse_all()

    if errors > 0:
        logger.warning(f"⚠️  有 {errors} 个错误")
        sys.exit(1)
    else:
        logger.success(f"✅ 成功！共 {changed} 个公告数据已更新")
        sys.exit(0)
