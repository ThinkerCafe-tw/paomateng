#!/usr/bin/env python3
import json

# Load data
with open('data/master.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"總公告數：{len(data)}\n")
print("=" * 80)
print("前 5 個公告的結構化資料提取結果：")
print("=" * 80)

for i, ann in enumerate(data[:5], 1):
    print(f"\n{i}. 公告標題：{ann['title'][:50]}")
    print(f"   發布日期：{ann['publish_date']}")
    print(f"   分類：{ann['classification']['category']}")
    print(f"   事件群組：{ann['classification']['event_group_id']}")
    print(f"   關鍵字：{', '.join(ann['classification']['keywords'][:3])}")

    ed = ann['version_history'][0]['extracted_data']
    print(f"\n   【提取的結構化資料】")
    print(f"   - report_version: {ed.get('report_version')}")
    print(f"   - event_type: {ed.get('event_type')}")
    print(f"   - status: {ed.get('status')}")
    print(f"   - affected_lines: {ed.get('affected_lines')}")
    print(f"   - affected_stations: {ed.get('affected_stations')[:3] if ed.get('affected_stations') else []}")
    print(f"   - predicted_resumption_time: {ed.get('predicted_resumption_time')}")
    print(f"   - actual_resumption_time: {ed.get('actual_resumption_time')}")

print("\n" + "=" * 80)
print("統計分析：")
print("=" * 80)

# Statistics
categories = {}
event_types = {}
has_predicted_time = 0

for ann in data:
    cat = ann['classification']['category']
    categories[cat] = categories.get(cat, 0) + 1

    ed = ann['version_history'][0]['extracted_data']
    et = ed.get('event_type')
    if et:
        event_types[et] = event_types.get(et, 0) + 1

    if ed.get('predicted_resumption_time'):
        has_predicted_time += 1

print(f"\n分類統計：")
for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    print(f"  {cat}: {count}")

print(f"\n事件類型統計：")
for et, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {et}: {count}")

print(f"\n包含預計復駛時間的公告：{has_predicted_time}/{len(data)} ({has_predicted_time/len(data)*100:.1f}%)")
