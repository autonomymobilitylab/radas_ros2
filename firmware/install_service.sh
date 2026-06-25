#!/bin/bash
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

set -a
source "$REPO_DIR/.env"
set +a

envsubst < "$REPO_DIR/systemd/radas_ros2.service.template" | sudo tee /etc/systemd/system/radas_ros2.service > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable radas_ros2.service
sudo systemctl start radas_ros2.service