#!/usr/bin/env bash
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

set -a
source "$REPO_DIR/.env"
set +a

envsubst < "$REPO_DIR/systemd/radas_ros2.service.template" | sudo tee /etc/systemd/system/radas_ros2.service > /dev/null

sudo mkdir $REPO_DIR/logs || true

sudo install -m 755 \
    "$REPO_DIR/systemd/start_radas_ros2.sh" \
    /usr/local/bin/start_radas_ros2.sh

sudo systemctl daemon-reload
sudo systemctl enable radas_ros2.service
sudo systemctl enable --now radas_ros2.service
sudo systemctl restart radas_ros2.service