# Rugged ATV Data Acquisition System (RADAS)

### **Collaborators:** 

 - [Aalto University](https://www.aalto.fi/en): Joel Ventola, Otto Peltonen

# Overview

The Rugged ATV Data Acquisition System, or RADAS, is a versatile, rugged sensor rack for ATVs.  

### **Sensors**
 - 32-channel 360° LIDAR: [Hesai XT32M2X](https://www.hesaitech.com/product/xt16-32-32m/)
 - 128-channel dome LIDAR: [Hesai JT128](https://www.hesaitech.com/product/jt128/)
 - 3 x RGB-cameras: [Basler a2A1920-51gcBAS](https://www.baslerweb.com/en/shop/a2a1920-51gcbas/)
 - NIR-camera: [Basler ace acA1300-60gmNIR](https://www.baslerweb.com/en/shop/aca1300-60gmnir/)
 - IMU: [VectorNav VN-100](https://www.vectornav.com/store/products/imu-ahrs/p/vn-100-rugged-imuahrs)
 - RTK-GPS: [Ardusimple simpleRTK 4 Heading](https://www.ardusimple.com/product/simplertk-4-heading/)

# Guide
Contains a lot of information on many tools used during development. Does not reflect the final deployed system.

### **Prerequisites**

- From [Ubuntu 24.04 Noble Numbat](https://releases.ubuntu.com/noble/)
- From [Docker version 29.5.2, build 79eb04c](https://github.com/docker/docker-install)

### **Pylonviewer quickstart outside of docker**

 1. Run pylonviewer from root:

 ```shell
 sudo /opt/pylon/bin/pylonviewer
 ```

 2. Run pylonviewer GigE configurator:

 `tools -> GigE configurator`

 Choose 
 `Optimize complete system`
 and then run `Configure`
 
> **Note:** if pylonviewer doesn't find the camera automatically you can use `f12` or `camera -> Add Remote GigE Camera` to add your camera manually.

 3. Reboot the system and relaunch pylonviewer to save the configuration settings. You're now able to see your attached cameras

 4. If this does not work, try using "Add remote GigE camera" and entering the camera's IP-address. Although, this speaks of a different underlying issue. 

### **Docker**

 1. Switch to firmware subfolder:

 ```shell
 cd ./firmware/
 ```

 2. Build the docker container:

 ```shell
 docker compose up --build -d
 ```

 3. Connect with a shell:

 ```shell
 docker compose exec ros2_dev /bin/bash
 ```

 4. If you want to use GUI apps inside the docker container run this before step 3. When running things remotely using ssh this needs to be ran on the local system before ssh connection is established.

 ```shell
 xhost +local:docker
 ```

 ### **Starting main ros package**
 1. Follow Docker startup instructions.

 2. Inside the container run:
 ```shell
 colcon build --packages-select radas_bringup --symlink-install
 ```

 3. Launching radas ros:
 ```shell
 ros2 launch radas_bringup bringup.launch.py
 ```

 ### **LIDARs** 

 **PandarView2:**

 1. Make sure device firewalls are turned off, or that LIDAR UDP-port (typically 2368) is allowed:

  ```shell
  sudo ufw disable
  sudo iptables -F
  ```

  > **Note:** Disconnecting and reconnecting the lidar will result in the firewall "resetting", after which you have to allow the port through again. 

 2. Check for wired IP-address:

  ```shell
  ip -br addr
  ```

  > **Note:** For troubleshooting/sanity-checking: you can check that the connected LIDAR is actually sending data to the port with ```sudo tcpdump -i <device_name> -n udp port 2368``` or just use Wireshark

 3. Hesai default IP-address is ```192.168.1.201``` which when connected to through a browser let's you control the LIDAR's parameters (for models that support WEB UI). Models that don't support this (such as JT128) need Hesai's LidarUtilities-software to control and change parameters. 

 4. Launch PandarView2 and choose "Listen for Data" (or Ctrl + R). Host IP can either be "any" or set it to your wired connection's address. 

 5. Once running, import the angle correction file. 

**Ros2 and Rviz2**

Same network setup as PandarView2-section. 

This guide won't go over creating the workspace, cloning manufacturer drivers/SDK or installing ROS package dependencies. Instead it will go over the most important config files changes for the LIDARs:

 1. Set IP-addresses. Device IP-address as your configured address, host address as your wired connection address and replace multicast address with just "". All addresses should be written in the form ```"192.168.1.xxx"``` , and as strings. 

 2. Clear these placeholder paths:

 ```yaml
 firetimes_path: ""
 ***
 channel_fov_filter_path: ""
 multi_fov_filter_ranges: ""
 ```

 3. Download corresponding device correction files and set their filepaths, for example:

 ```yaml
 correction_file_path: "/home/user/hesai_ws/config/jt128_correction.csv" 
 ```

 4. Make sure that the point cloud is actually sent through ros

 ```yaml
 ros:
    ros_frame_id: hesai_lidar 
    ***
    send_packet_ros: true                               
    send_point_cloud_ros: true                           
    send_imu_ros: true   
 ```

 5. Check if your frame frequency is set to 0. If it is, change it to a suitable value:

 ```yaml
 frame_frequency: 10                   
 default_frame_frequency: 10.0
 ```
 6. Launch the node and run Rviz2. Useful troubleshooting checks include:

 ```shell
 ros2 topic list
 ```

 You should see topics such as ```/lidar_points```. Check for topic info and hz:

 ```shell
 ros2 topic info /lidar_points
 ros2 topic hz /lidar_points
 ```

 ```ros2 topic info /lidar_points``` should return 

 ```shell
 Type: sensor_msgs/msg/PointCloud2
 Publisher count: 1
 Subscription count: 1
 ```

 If hz doesn't return anything, ros is not actually receiving the lidar datastream. 
> **Note:** ros2 topic hz takes a few moments to calculate the frequency of data, don't expect instantaneous result.

 ### **PTP**
 **Setting up nuc as PTP grandmaster**

 PTP is automatically set up when running ```docker compose up --build -d``` in a secondary container parallel to the main ros2 container. If you wish to manually broadcast PTP from your device for testing etc you can use:
 ```shell
 sudo PTP4l -i <device> -m -S
 ```
 
 The automatic PTP setup assumes that you have an ```.env``` file in your ```./firmware``` folder with the key ```PTP_INTERFACE=<device>```

 Both the JT128 and XT32M lidars format their timestamps in the data stream the same way, which you can find with the following steps.
 1. From the end of the data packet find the manufacturer magic number ```42```.
 2. Move back 10 bits.
 3. First bit is ```year - 1900```.
 4. Next 5 bits are in the order of: ```month, day, hour, minute, second```.
 5. Next 4 bits are the microsecond part of UTC.

 ### **SSH access to NUC**
 The MS-01 NUC is set to accept SSH traffic on the default port. Connection details can be found physically on the machine. If a display is required, add the `-X` flag before `username@ip`.

 For ease of development, local changes can be pushed to the NUC using `./firmware/sync_to_nuc.sh`. This allows changes made on the local system to be pushed to the NUC without going through GitHub.
 
 This script should only be used during development and for quick tests. **Working, finalized code should always be manually committed and pulled to the NUC.** Before pulling on the NUC, run `git restore .` to revert to the latest published version.

 ### **Running RADAS automatically on startup with systemd**
 The ROS 2 Docker stack can be started automatically on boot using the `systemd` service.
 
 The `.env` file should include:
 
 ```shell
 PROJECT_DIR=/path/to/firmware/folder
 SERVICE_USER=localUser
 ```
 
 Make the installer executable and install the service:
 
 ```shell
 chmod +x install_service.sh
 ./install_service.sh
 ```
 
 Start the service manually:
 
 ```shell
 sudo systemctl start radas_ros2.service
 ```
 
 Follow logs:
 
 ```shell
 journalctl -u radas_ros2.service -f
 ```
 
 Restart the service after changes:
 
 ```shell
 sudo systemctl restart radas_ros2.service
 ```
 
 Disable autostart:
 
 ```shell
 sudo systemctl disable radas_ros2.service
 ```
 
 Remove the service completely:
 
 ```shell
 sudo systemctl stop radas_ros2.service
 sudo systemctl disable radas_ros2.service
 sudo rm /etc/systemd/system/radas_ros2.service
 sudo systemctl daemon-reload
 ```
 