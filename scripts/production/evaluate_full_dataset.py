#!/usr/bin/env python3
"""
完整数据集评估脚本
分析 master.json 中所有公告的时间提取性能
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def analyze_dataset():
    """分析完整数据集的时间提取情况"""

    data_file = project_root / "data" / "master.json"

    print("=" * 100)
    print("📊 完整数据集评估报告")
    print("=" * 100)

    # Load data
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\n总公告数: {len(data)}")

    # Statistics
    stats = {
        'total': len(data),
        'with_predicted': 0,
        'with_actual': 0,
        'with_both': 0,
        'with_neither': 0,
        'predicted_times': [],
        'actual_times': [],
        'categories': defaultdict(int),
        'event_types': defaultdict(int),
        'status_types': defaultdict(int),
    }

    # Analyze each announcement
    for ann in data:
        title = ann['title']
        latest = ann['version_history'][0]
        extracted = latest['extracted_data']

        predicted = extracted.get('predicted_resumption_time')
        actual = extracted.get('actual_resumption_time')

        if predicted:
            stats['with_predicted'] += 1
            stats['predicted_times'].append({
                'title': title,
                'time': predicted,
                'report_version': extracted.get('report_version')
            })

        if actual:
            stats['with_actual'] += 1
            stats['actual_times'].append({
                'title': title,
                'time': actual,
                'report_version': extracted.get('report_version')
            })

        if predicted and actual:
            stats['with_both'] += 1
        elif not predicted and not actual:
            stats['with_neither'] += 1

        # Category distribution
        category = ann.get('classification', {}).get('category', 'Unknown')
        stats['categories'][category] += 1

        # Event type distribution
        event_type = extracted.get('event_type')
        if event_type:
            stats['event_types'][event_type] += 1

        # Status distribution
        status = extracted.get('status')
        if status:
            stats['status_types'][status] += 1

    # Print results
    print("\n" + "=" * 100)
    print("📈 时间提取统计")
    print("=" * 100)

    print(f"\n包含预测恢复时间: {stats['with_predicted']:>3} / {stats['total']:>3} ({stats['with_predicted']/stats['total']*100:>5.1f}%)")
    print(f"包含实际恢复时间: {stats['with_actual']:>3} / {stats['total']:>3} ({stats['with_actual']/stats['total']*100:>5.1f}%)")
    print(f"两者都有:         {stats['with_both']:>3} / {stats['total']:>3} ({stats['with_both']/stats['total']*100:>5.1f}%)")
    print(f"两者都无:         {stats['with_neither']:>3} / {stats['total']:>3} ({stats['with_neither']/stats['total']*100:>5.1f}%)")

    # Category distribution
    print("\n" + "=" * 100)
    print("📂 公告分类分布")
    print("=" * 100)
    for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
        print(f"{category:30s}: {count:3d} ({count/stats['total']*100:5.1f}%)")

    # Event type distribution
    if stats['event_types']:
        print("\n" + "=" * 100)
        print("🌧️  事件类型分布")
        print("=" * 100)
        for event_type, count in sorted(stats['event_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"{event_type:30s}: {count:3d}")

    # Status distribution
    if stats['status_types']:
        print("\n" + "=" * 100)
        print("🚦 运营状态分布")
        print("=" * 100)
        for status, count in sorted(stats['status_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"{status:30s}: {count:3d}")

    # Sample predicted times
    print("\n" + "=" * 100)
    print("🔮 预测恢复时间示例 (前10条)")
    print("=" * 100)
    for i, item in enumerate(stats['predicted_times'][:10], 1):
        time_str = item['time'].split('T')[1][:5] if 'T' in item['time'] else item['time']
        report_ver = f"第{item['report_version']}报" if item['report_version'] else ""
        print(f"{i:2d}. {time_str} | {report_ver:6s} | {item['title'][:70]}")

    # Sample actual times
    print("\n" + "=" * 100)
    print("✅ 实际恢复时间示例 (前10条)")
    print("=" * 100)
    for i, item in enumerate(stats['actual_times'][:10], 1):
        time_str = item['time'].split('T')[1][:5] if 'T' in item['time'] else item['time']
        report_ver = f"第{item['report_version']}报" if item['report_version'] else ""
        print(f"{i:2d}. {time_str} | {report_ver:6s} | {item['title'][:70]}")

    # Save detailed report
    report_file = project_root / "data" / "evaluation_report.json"
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_announcements": stats['total'],
            "with_predicted": stats['with_predicted'],
            "with_actual": stats['with_actual'],
            "with_both": stats['with_both'],
            "with_neither": stats['with_neither'],
            "predicted_rate": round(stats['with_predicted']/stats['total']*100, 2),
            "actual_rate": round(stats['with_actual']/stats['total']*100, 2),
        },
        "categories": dict(stats['categories']),
        "event_types": dict(stats['event_types']),
        "status_types": dict(stats['status_types']),
        "predicted_times_count": len(stats['predicted_times']),
        "actual_times_count": len(stats['actual_times']),
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 100)
    print(f"📄 详细报告已保存: {report_file}")
    print("=" * 100)

    return stats


if __name__ == "__main__":
    stats = analyze_dataset()

    print("\n✅ 评估完成！")
    print("=" * 100)
