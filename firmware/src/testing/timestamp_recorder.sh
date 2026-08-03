#!/bin/bash
ros2 topic echo --once /Basler_middle/pylon_ros2_camera_node/image_raw/header \
  > topic1.txt
