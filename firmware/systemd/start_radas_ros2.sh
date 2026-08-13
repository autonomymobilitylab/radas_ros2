#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="${PROJECT_DIR}/logs"
CURRENT="$LOG_DIR/current_boot.log"
PREVIOUS="$LOG_DIR/previous_boot.log"

set -a
source "${PROJECT_DIR}/.env"
set +a

mkdir -p "$LOG_DIR"

# Preserve the previous boot's log
if [ -f "$CURRENT" ]; then
    mv -f "$CURRENT" "$PREVIOUS"
fi

# Start compose and log everything
exec docker compose --ansi never up 2>&1 | tee -a "$CURRENT"