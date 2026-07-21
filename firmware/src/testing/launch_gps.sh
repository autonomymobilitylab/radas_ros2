#!/bin/bash

source /ros2_ws/src/.env

str2str -in "ntrip://${NTRIPUSER}:${NTRIPPASS}@opencaster.nls.fi:2101/VRS-FKP" -out "serial://ttyACM0:115200:8:n:1:of" -p 60.188333 24.823917 4 -n 5000 -t 3 &
ros2 launch septentrio_gnss_driver rover.launch.py file_name:=custom_rover.yaml