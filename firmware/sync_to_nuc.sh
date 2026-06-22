#!/bin/bash
source "$(dirname "$0")/.env"
rsync -avz --exclude-from=".rsync_exclude" --progress ./ $REMOTE_USER@$REMOTE_HOST:$REMOTE_FIRMWARE_PATH