# Data Schema Documentation

## Overview

The Railway News Monitor outputs data to `data/master.json` in a structured JSON format. This document describes the complete schema.

## Top-Level Structure

The JSON file contains an array of `Announcement` objects:

```json
[
  { /* Announcement 1 */ },
  { /* Announcement 2 */ },
  ...
]
```

## Announcement Object

Each announcement contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (same as newsNo from TRA URL) |
| `title` | string | Announcement title |
| `publish_date` | string | Publication date in YYYY/MM/DD format |
| `detail_url` | string | Full URL to announcement detail page |
| `classification` | object | Classification metadata (see below) |
| `version_history` | array | Array of version snapshots (see below) |

### Classification Object

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | One of: `Disruption_Suspension`, `Disruption_Update`, `Disruption_Resumption`, `General_Operation` |
| `keywords` | array[string] | Matched keywords from classification rules |
| `event_group_id` | string | Event identifier in format `YYYYMMDD_EventName` |

### Version Entry Object

Each entry in `version_history` represents a snapshot of the announcement at a specific time:

| Field | Type | Description |
|-------|------|-------------|
| `scraped_at` | string | ISO 8601 timestamp when this version was captured (Asia/Taipei timezone) |
| `content_html` | string | Raw HTML content of the announcement |
| `content_hash` | string | MD5 hash of content_html in format `md5:<hexdigest>` |
| `extracted_data` | object | Structured data extracted from HTML (see below) |

### Extracted Data Object

The core research data - 7 fields extracted from announcement content:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `report_version` | string \| null | Report number | `"1"`, `"2"`, `"第3發"` |
| `event_type` | string \| null | Event category | `"Typhoon"`, `"Heavy_Rain"`, `"Earthquake"`, `"Equipment_Failure"` |
| `status` | string \| null | Operational status | `"Suspended"`, `"Partial_Operation"`, `"Resumed_Single_Track"`, `"Resumed_Normal"` |
| `affected_lines` | array[string] | List of affected railway lines | `["西部幹線", "東部幹線"]` |
| `affected_stations` | array[string] | List of affected stations | `["二水", "林內"]` |
| `predicted_resumption_time` | string \| null | **KEY FIELD** - Estimated resumption time (ISO 8601) | `"2025-10-21T19:00:00+08:00"` |
| `actual_resumption_time` | string \| null | Actual resumption time (ISO 8601) | `"2025-10-21T17:28:00+08:00"` |

**Note**: Any field that fails extraction will be `null`.

## Complete Example

```json
[
  {
    "id": "8ae4cac399fde98e019a05318e506ed0",
    "title": "平溪線因豪雨暫停營運　臺鐵持續監測確保行車安全",
    "publish_date": "2025/10/21",
    "detail_url": "https://www.railway.gov.tw/tra-tip-web/tip/tip009/tip911/newsDtl?newsNo=8ae4cac399fde98e019a05318e506ed0",
    "classification": {
      "category": "Disruption_Suspension",
      "keywords": ["平溪線", "豪雨", "暫停營運"],
      "event_group_id": "20251021_平溪線"
    },
    "version_history": [
      {
        "scraped_at": "2025-10-21T15:00:00+08:00",
        "content_html": "<div class=\"newsContent\"><p>因豪雨影響，平溪線暫停營運，預計今日19:00恢復行駛...</p></div>",
        "content_hash": "md5:b1d5a8c4f9e3f0a1",
        "extracted_data": {
          "report_version": "1",
          "event_type": "Heavy_Rain",
          "status": "Suspended",
          "affected_lines": ["平溪線"],
          "affected_stations": [],
          "predicted_resumption_time": "2025-10-21T19:00:00+08:00",
          "actual_resumption_time": null
        }
      },
      {
        "scraped_at": "2025-10-21T15:30:10+08:00",
        "content_html": "<div class=\"newsContent\"><p>因豪雨持續，平溪線暫停營運，預計今日20:00恢復行駛...</p></div>",
        "content_hash": "md5:c8e0d7b2a9b3c1f4",
        "extracted_data": {
          "report_version": "1",
          "event_type": "Heavy_Rain",
          "status": "Suspended",
          "affected_lines": ["平溪線"],
          "affected_stations": [],
          "predicted_resumption_time": "2025-10-21T20:00:00+08:00",
          "actual_resumption_time": null
        }
      }
    ]
  }
]
```

## Research Applications

### Tracking Time Estimate Evolution

The `version_history` array allows researchers to analyze how `predicted_resumption_time` changes:

```python
# Example: Extract all predicted times for an event
for version in announcement["version_history"]:
    predicted_time = version["extracted_data"]["predicted_resumption_time"]
    scraped_at = version["scraped_at"]
    print(f"At {scraped_at}, TRA predicted: {predicted_time}")
```

Output:
```
At 2025-10-21T15:00:00+08:00, TRA predicted: 2025-10-21T19:00:00+08:00
At 2025-10-21T15:30:10+08:00, TRA predicted: 2025-10-21T20:00:00+08:00
```

### Event Sequence Reconstruction

Use `event_group_id` to find all announcements for a single event:

```python
event_id = "20251021_平溪線"
related_announcements = [
    a for a in announcements
    if a["classification"]["event_group_id"] == event_id
]
```

## Data Validation

All data conforms to Pydantic models defined in `src/models/announcement.py`. Invalid data will fail validation during load/save operations.

## Backup Policy

Backups are created in `data/backups/` before each write operation with timestamp format: `master_backup_YYYYMMDD_HHMMSS.json`
