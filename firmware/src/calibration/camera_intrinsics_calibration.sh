#!/bin/bash

read -p "Enter camera position ['left', 'middle', 'right'] to calculate intrinsics for: " camera_position
ros2 run camera_calibration cameracalibrator --size 8x11 --square 0.60 --no-service-check image:=Basler_$camera_position/pylon_ros2_camera_node/image_raw camera:=/Basler_$camera_position/pylon_ros2_camera_node
read -p "Calibration complete. Press any key to override the existing calibration file, or Ctrl+C to cancel." -n1 -s
tar -xzf /tmp/calibrationdata.tar.gz -C /ros2_ws/config/instrinsics/$camera_position/
