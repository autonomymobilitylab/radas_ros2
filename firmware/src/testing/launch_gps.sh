#!/bin/bash

cp /ros2_ws/config/custom_rover.yaml /opt/ros/jazzy/share/septentrio_gnss_driver/config/custom_rover.yaml
ros2 launch septentrio_gnss_driver rover.launch.py file_name:=custom_rover.yaml