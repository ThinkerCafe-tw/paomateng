#!/bin/bash

# Trigger GitHub Actions workflow for paomateng monitoring
# This script is designed to be run by cron every 5 minutes

# Load GitHub token from resume/.env if not set
if [ -z "$GITHUB_TOKEN" ]; then
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  ENV_FILE="$SCRIPT_DIR/../resume/.env"
  if [ -f "$ENV_FILE" ]; then
    export $(grep GITHUB_TOKEN "$ENV_FILE" | xargs)
  fi
fi

REPO_OWNER="ThinkerCafe-tw"
REPO_NAME="paomateng"
WORKFLOW_ID="monitor.yml"

# Log file
LOG_FILE="$HOME/paomateng-cron.log"

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting workflow trigger..." >> "$LOG_FILE"

# Trigger the workflow
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/workflows/$WORKFLOW_ID/dispatches" \
  -d '{"ref":"main"}')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" -eq 204 ]; then
  echo "[$TIMESTAMP] ✅ Successfully triggered workflow (HTTP $HTTP_CODE)" >> "$LOG_FILE"
else
  echo "[$TIMESTAMP] ❌ Failed to trigger workflow (HTTP $HTTP_CODE)" >> "$LOG_FILE"
  echo "$RESPONSE" >> "$LOG_FILE"
fi
