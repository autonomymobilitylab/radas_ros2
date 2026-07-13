#!/bin/bash

read -p "Enter camera name to calculate intrinsics for: " camera_name
ros2 run camera_calibration cameracalibrator --size 8x11 --square 0.60 --no-service-check image:=$camera_name/pylon_ros2_camera_node/image_raw camera:=/$camera_name/pylon_ros2_camera_node