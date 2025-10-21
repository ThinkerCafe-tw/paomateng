# Deployment Guide

## Local Development Deployment

### Prerequisites

- Python 3.10+
- Git
- 10GB free disk space (for historical data + backups)

### Setup Steps

```bash
# 1. Navigate to project directory
cd /path/to/railway-news-monitor

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify installation
python -m src.main --help

# 6. Test configuration
python -c "import yaml; yaml.safe_load(open('config/settings.yaml'))"
```

### Running Historical Scrape (One-Time)

```bash
# Activate venv first
source venv/bin/activate

# Run scrape
python -m src.main --mode historical

# Monitor progress in logs/
tail -f logs/railway_monitor.log
```

Expected duration: 2-3 hours for full scrape.

## Server Deployment (Linux)

### Option 1: systemd Service (Recommended)

Create systemd service file for continuous monitoring:

```bash
# Create service file
sudo nano /etc/systemd/system/railway-monitor.service
```

Content:

```ini
[Unit]
Description=Railway News Monitor
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/railway-news-monitor
Environment="PATH=/home/your-username/railway-news-monitor/venv/bin"
ExecStart=/home/your-username/railway-news-monitor/venv/bin/python -m src.main --mode monitor
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable railway-monitor

# Start service
sudo systemctl start railway-monitor

# Check status
sudo systemctl status railway-monitor

# View logs
sudo journalctl -u railway-monitor -f
```

### Option 2: Cron Job

For scheduled executions instead of continuous monitoring:

```bash
crontab -e
```

Add:

```cron
# Run monitoring cycle every 5 minutes
*/5 * * * * cd /home/user/railway-news-monitor && venv/bin/python -m src.main --mode monitor --interval 1 >> logs/cron.log 2>&1

# Run full historical scrape weekly (Sunday 2 AM)
0 2 * * 0 cd /home/user/railway-news-monitor && venv/bin/python -m src.main --mode historical >> logs/weekly-scrape.log 2>&1
```

## Docker Deployment (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data data/backups logs

# Run monitoring mode by default
CMD ["python", "-m", "src.main", "--mode", "monitor"]
```

Build and run:

```bash
# Build image
docker build -t railway-monitor .

# Run container
docker run -d \
  --name railway-monitor \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  railway-monitor

# View logs
docker logs -f railway-monitor

# Stop
docker stop railway-monitor
```

## Backup Strategy

### Automated Backups

The system automatically creates backups in `data/backups/` before each write to `master.json`.

### Manual Backup Schedule

Recommended external backup schedule:

```bash
#!/bin/bash
# backup.sh - Create timestamped backup

BACKUP_DIR="/backups/railway-monitor"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup data
cp -r data $BACKUP_DIR/data_$TIMESTAMP

# Backup logs
cp -r logs $BACKUP_DIR/logs_$TIMESTAMP

# Keep only last 30 days
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;
```

Add to cron:

```cron
0 3 * * * /home/user/railway-monitor/backup.sh
```

## Recovery Procedures

### Recover from Backup

```bash
# Stop service
sudo systemctl stop railway-monitor

# Restore from backup
cp data/backups/master_backup_YYYYMMDD_HHMMSS.json data/master.json

# Restart service
sudo systemctl start railway-monitor
```

### Corrupted JSON Recovery

```bash
# Validate JSON
python -m json.tool data/master.json > /dev/null

# If invalid, find latest valid backup
cd data/backups
for file in $(ls -t master_backup_*.json); do
    if python -m json.tool $file > /dev/null 2>&1; then
        echo "Latest valid backup: $file"
        cp $file ../master.json
        break
    fi
done
```

## Monitoring and Health Checks

### Log Monitoring

```bash
# Check for errors
grep ERROR logs/railway_monitor.log | tail -20

# Check recent activity
tail -100 logs/railway_monitor.log

# Monitor in real-time
tail -f logs/railway_monitor.log | grep -E "(NEW|CHANGE|ERROR)"
```

### Data Quality Checks

```bash
# Count announcements
python -c "import json; data=json.load(open('data/master.json')); print(f'Total announcements: {len(data)}')"

# Check latest update
python -c "import json; from datetime import datetime; data=json.load(open('data/master.json')); latest=max(a['version_history'][-1]['scraped_at'] for a in data if a['version_history']); print(f'Latest scrape: {latest}')"
```

### Health Check Script

Create `scripts/health_check.sh`:

```bash
#!/bin/bash

# Check if process is running
if systemctl is-active --quiet railway-monitor; then
    echo "✓ Service is running"
else
    echo "✗ Service is NOT running"
    exit 1
fi

# Check log for recent activity (last 10 minutes)
if tail -100 logs/railway_monitor.log | grep -q "$(date -d '10 minutes ago' +'%Y-%m-%d %H')"; then
    echo "✓ Recent activity detected"
else
    echo "⚠ No activity in last 10 minutes"
fi

# Check disk space
DISK_USAGE=$(df -h data | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 90 ]; then
    echo "✓ Disk space OK ($DISK_USAGE%)"
else
    echo "⚠ Disk space critical ($DISK_USAGE%)"
fi

# Check JSON validity
if python -m json.tool data/master.json > /dev/null 2>&1; then
    echo "✓ JSON is valid"
else
    echo "✗ JSON is CORRUPTED"
    exit 1
fi
```

Run via cron every hour:

```cron
0 * * * * /home/user/railway-news-monitor/scripts/health_check.sh >> logs/health.log 2>&1
```

## Troubleshooting

### Service Won't Start

```bash
# Check systemd status
sudo systemctl status railway-monitor

# Check Python environment
/path/to/venv/bin/python -m src.main --help

# Check permissions
ls -la data/ logs/
```

### High Memory Usage

```bash
# Check process memory
ps aux | grep python

# Restart service
sudo systemctl restart railway-monitor
```

### Network Issues

```bash
# Test TRA website connectivity
curl -I https://www.railway.gov.tw/tra-tip-web/tip/tip009/tip911/newsList?page=0

# Check DNS
nslookup www.railway.gov.tw

# Increase retry attempts in config/settings.yaml
retry_attempts: 5
rate_limit_delay: 2.0
```

## Production Checklist

Before deploying to production:

- [ ] Run historical scrape successfully on test environment
- [ ] Verify all extracted_data fields are populated correctly
- [ ] Test monitoring mode for at least 24 hours
- [ ] Set up systemd service or cron jobs
- [ ] Configure automated backups
- [ ] Set up log rotation (loguru handles this automatically)
- [ ] Document any custom configuration changes
- [ ] Set up monitoring alerts (optional: email on errors)
- [ ] Verify disk space requirements (estimate: 1GB per 10,000 announcements)
- [ ] Test recovery procedures

## Monitoring Alerts (Optional)

Email alerts on errors:

```python
# Add to src/utils/logger.py

from loguru import logger
import smtplib
from email.mime.text import MIMEText

def send_alert(message):
    msg = MIMEText(message)
    msg['Subject'] = 'Railway Monitor Alert'
    msg['From'] = 'monitor@example.com'
    msg['To'] = 'admin@example.com'

    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()

# Add custom handler for ERROR level
logger.add(send_alert, level="ERROR", format="{message}")
```

## Performance Tuning

### For Large Datasets

If dataset exceeds 50,000 announcements:

1. Increase monitoring interval: `interval_minutes: 10`
2. Reduce pages to check: `max_pages_to_check: 1`
3. Consider database storage instead of JSON (requires code modification)

### Rate Limiting Adjustments

If getting blocked by TRA:

```yaml
scraper:
  rate_limit_delay: 2.0  # Increase to 2 seconds
  retry_attempts: 5      # More retries
```

## Contact and Support

For deployment issues, consult:
- Logs: `logs/railway_monitor.log`
- Design document: `.spec-workflow/specs/railway-news-monitor/design.md`
- Requirements: `.spec-workflow/specs/railway-news-monitor/requirements.md`
