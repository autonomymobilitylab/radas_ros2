#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="/Basler_middle"
NODE="/Basler_middle/pylon_ros2_camera_node"

wait_for_service() {
    local service="$1"

    until ros2 service list | grep -Fxq "$service"; do
        echo "Waiting for ROS 2 service: $service"
        sleep 1
    done
}

TRIGGER_SOURCE_SERVICE="${NODE}/set_trigger_source"
TRIGGER_MODE_SERVICE="${NODE}/set_trigger_mode"

wait_for_service "$TRIGGER_MODE_SERVICE"
wait_for_service "$TRIGGER_SOURCE_SERVICE"

echo "Setting trigger source to Line1..."
ros2 service call \
  "$TRIGGER_SOURCE_SERVICE" \
  pylon_ros2_camera_interfaces/srv/SetIntegerValue \
  "{value: 1}"

echo "Enabling trigger mode..."
ros2 service call \
  "$TRIGGER_MODE_SERVICE" \
  std_srvs/srv/SetBool \
  "{data: true}"

echo "Basler_middle configured for hardware triggering on Line 1."