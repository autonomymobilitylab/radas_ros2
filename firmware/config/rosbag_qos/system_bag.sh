#!/bin/bash
ros2 bag record \
  /Basler_left/pylon_ros2_camera_node/image_raw \
  /Basler_middle/pylon_ros2_camera_node/image_raw \
  /Basler_right/pylon_ros2_camera_node/image_raw \
  /Basler_left/pylon_ros2_camera_node/camera_info \
  /Basler_middle/pylon_ros2_camera_node/camera_info \
  /Basler_right/pylon_ros2_camera_node/camera_info \
  /lidar_points_xt \
  /lidar_points_jt \
  /imu/acceleration_hr \
  /imu/angular_velocity_hr \
  /imu/mag \
  /Gnss/gpsfix \
  /tf_static \