# Railway News Monitor

Taiwan Railway Administration (TRA) announcement tracking and analysis system for academic research.

## Overview

This system automatically monitors TRA's public announcements, tracking service disruptions and analyzing how crisis communications evolve over time. It serves Professor Lin's research on crisis communication patterns.

### Key Features

- ✅ **Historical Data Collection**: Scrape all existing TRA announcements
- ✅ **Continuous Monitoring**: Detect new announcements and content changes
- ✅ **Content Change Detection**: Track modifications to existing announcements via hash comparison
- ✅ **Structured Data Extraction**: Parse 7 key fields from announcements:
  - Report version (第1報, 第2報...)
  - Event type (Typhoon, Heavy Rain, Earthquake, Equipment Failure)
  - Operational status (Suspended, Partial Operation, Resumed)
  - Affected lines and stations
  - **Predicted resumption time** (primary research target)
  - Actual resumption time
- ✅ **Event Grouping**: Link related announcements (Report #1, #2, #3...) under single event ID
- ✅ **Atomic JSON Storage**: Reliable data persistence with file locking

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Setup

```bash
# Clone or navigate to project directory
cd railway-news-monitor

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m src.main --help
```

## Quick Start

### 1. Historical Scrape (Initial Data Collection)

```bash
python -m src.main --mode historical
```

This will:
- Scrape all announcement list pages from TRA website
- Extract structured data from each announcement
- Save to `data/master.json`

**Note**: This may take 2-3 hours depending on the number of announcements and rate limiting.

### 2. Monitoring Mode (Continuous Updates)

```bash
# Run with default 5-minute interval
python -m src.main --mode monitor

# Run with custom 10-minute interval
python -m src.main --mode monitor --interval 10
```

This will:
- Check first 2 pages every N minutes
- Detect new announcements
- Detect content changes via hash comparison
- Append new versions to `version_history`

Press `Ctrl+C` to stop monitoring.

## Configuration

Edit `config/settings.yaml` to customize behavior:

```yaml
scraper:
  base_url: "https://www.railway.gov.tw/tra-tip-web/tip/tip009/tip911"
  user_agent: "TRA News Monitor (Research Project - Professor Lin)"
  request_timeout: 30
  retry_attempts: 3
  rate_limit_delay: 1.0  # seconds between requests

monitoring:
  interval_minutes: 5
  max_pages_to_check: 2

storage:
  output_file: "data/master.json"
  backup_dir: "data/backups"
  pretty_print: true

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  log_file: "logs/railway_monitor.log"
  rotation: "10 MB"
```

## Output Data Schema

See `docs/DATA_SCHEMA.md` for complete JSON structure documentation.

### Example Announcement

```json
{
  "id": "8ae4cac399fde98e019a05318e506ed0",
  "title": "平溪線因豪雨暫停營運",
  "publish_date": "2025/10/21",
  "detail_url": "https://...",
  "classification": {
    "category": "Disruption_Suspension",
    "keywords": ["平溪線", "豪雨", "暫停營運"],
    "event_group_id": "20251021_Pingxi_Rain"
  },
  "version_history": [
    {
      "scraped_at": "2025-10-21T15:00:00+08:00",
      "content_html": "<div>...</div>",
      "content_hash": "md5:b1d5...f4a1",
      "extracted_data": {
        "report_version": "1",
        "event_type": "Heavy_Rain",
        "status": "Suspended",
        "affected_lines": ["平溪線"],
        "predicted_resumption_time": "2025-10-21T19:00:00+08:00"
      }
    }
  ]
}
```

## Usage Documentation

See `docs/USAGE.md` for detailed usage examples and workflows.

## Architecture

```
railway-news-monitor/
├── src/
│   ├── models/          # Pydantic data models
│   ├── utils/           # HTTP client, hash, date parsing
│   ├── scrapers/        # List and detail page scrapers
│   ├── parsers/         # Content extraction (7 fields)
│   ├── classifiers/     # Keyword-based classification
│   ├── storage/         # JSON persistence with locking
│   ├── orchestrator/    # Historical & monitoring workflows
│   └── main.py          # CLI entry point
├── config/              # Configuration files
├── data/                # Output JSON and backups
├── logs/                # Application logs
└── tests/               # Test suite
```

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black src/

# Lint
flake8 src/

# Type check
mypy src/
```

## Troubleshooting

### Common Issues

1. **Network Errors**: Check your internet connection and TRA website availability
2. **Rate Limiting**: Increase `rate_limit_delay` in config if getting connection errors
3. **Permission Errors**: Ensure write permissions for `data/` and `logs/` directories

### Logs

Check `logs/railway_monitor.log` for detailed operation logs.

## Research Use

This system is designed for academic research. The extracted `predicted_resumption_time` field enables analysis of:
- How time estimates evolve across sequential reports
- Accuracy of initial predictions vs. actual resumption times
- Communication patterns during different types of disruptions

## License

For academic research use.

## Contact

For questions or issues, contact the research team.
