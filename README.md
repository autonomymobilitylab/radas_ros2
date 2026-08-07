# Rugged ATV Data Acquisition System (RADAS)

### **Collaborators:**

 - [Aalto University Autonomy & Mobility Lab](https://www.aalto.fi/en/department-of-energy-and-mechanical-engineering/autonomy-mobility-lab): Joel Ventola, Otto Peltonen

# Overview

The Rugged ATV Data Acquisition System, or RADAS, is a versatile, rugged sensor rack designed to be mounted on the front cargo area of an ATV. With its modular design and small footprint, the system can also be mounted on other vehicles and platforms.

The purpose of this system is to collect real-world data for state-of-the-art (SOTA) datasets in unstructured off-road environments, such as forests and other urban areas in Finland.

The system includes two different LiDAR sensors, three RGB cameras that provide a 170° field of view, a 9-DoF IMU, and an RTK-capable GNSS receiver. The system is also planned to be upgraded with an additional NIR (near-infrared) camera in the future.
The sensors and their specifications are listed in more detail in the table below.

### **Sensors**
 - 32-channel 360° LIDAR: [Hesai XT32M2X](https://www.hesaitech.com/product/xt16-32-32m/)
 - 128-channel dome LIDAR: [Hesai JT128](https://www.hesaitech.com/product/jt128/)
 - 3 x RGB-cameras: [Basler a2A1920-51gcBAS](https://www.baslerweb.com/en/shop/a2a1920-51gcbas/)
 - IMU: [Xsens MTi-320-3A-SK](https://www.xsens.com/sensor-modules/xsens-mti-320)
 - RTK-GPS: [Ardusimple simpleRTK 4 Heading](https://www.ardusimple.com/product/simplertk-4-heading/)

# Guide
This guide contains information about many of the tools and procedures used during development. It does not necessarily reflect the final deployed system.

## **Prerequisites**

- [Ubuntu 24.04 LTS (Noble Numbat)](https://releases.ubuntu.com/noble/)
- [Docker 29.5.2, build 79eb04c](https://github.com/docker/docker-install)

## **Installation**
 1. Make sure you have the prerequisites listed above installed.

 2. Clone the repository and navigate to the `firmware` directory:

 ```shell
 git clone https://github.com/joevento/radas_ros2.git
 cd ./radas_ros2/firmware
 ```

 3. Manually start the container to make sure everything works as intended:

 ```shell
 docker compose up --build
 ```

 4. Once the container has started successfully, navigate to `http://localhost:8080/` to access the system's web interface. Each sensor is displayed in its own table, with a traffic light indicator in the first column showing its general status. Verify that all sensors show a green status.

 5. Once the system's functionality has been verified, stop the container using `Ctrl+C`.

 6. Configure the NUC's network interface with the following static network settings:

    * **IP address:** `192.168.1.2`
    * **Subnet mask:** `255.255.255.0`

    Once configured, the system's web interface can be accessed remotely at `http://192.168.1.2:8080/`.


 7. **(Optional)** Create an unprivileged user account under which the system will run.

 8. Regardless of whether you completed the optional step above, make sure the account used to run the system is automatically logged in at startup. This prevents the NUC from getting stuck on the login screen when the system is powered on.

    Automatic login can be enabled in the Ubuntu settings under:

    `System -> Users -> Automatic Login`

 > **Note:** If the Users page is grayed out, click the **"Unlock..."** button in the top-right corner.

 9. Once the functionality of the system has been verified manually, run the systemd user service installation script from the `firmware` directory:

 ```shell
 ./install_service.sh
 ```

 The script installs and enables the systemd user service responsible for starting the RADAS ros2 system automatically when the user logs in.

 10. Once the service has been installed successfully, restart the NUC and enter the BIOS (typically by pressing `F2` or `Del`). In the BIOS, enable automatic startup when power is restored.

     On the MS-01, this setting can be found under:

     `Advanced -> ACPI -> Restore Power on AC Power Loss`

     This ensures that the NUC boots and subsequently logs in automatically when the main power switch is turned on.

 11. Save the BIOS settings and exit. Allow the system to boot into Ubuntu, then navigate to `http://localhost:8080/` (or `http://192.168.1.2:8080/` when accessing remotely) and verify that all sensor status indicators are green.

 12. The system is now ready for use. From this point onward, it will automatically boot, log in, and start the RADAS ros2 system when the power switch on the side of the electrical cabinet is turned on.

 > **Note:** It has been measured that, from a cold and dark state, the system takes approximately two (2) minutes to start before data acquisition can begin.

## General Testing and Development Tools

### **Pylon Viewer Quick Start Outside of Docker**

 1. Run Pylon Viewer as root:

 ```shell
 sudo /opt/pylon/bin/pylonviewer
 ```

 2. Open the Pylon Viewer GigE Configurator:

    `Tools -> GigE Configurator`

    Select:

    `Optimize Complete System`

    Then click:

    `Configure`

 > **Note:** If Pylon Viewer does not detect the camera automatically, press `F12` or navigate to `Camera -> Add Remote GigE Camera` to add the camera manually.

 3. Reboot the system and relaunch Pylon Viewer to apply the configuration. The connected cameras should now be visible in Pylon Viewer.

### **Docker**

 1. Switch to firmware subfolder:

 ```shell
 cd ./firmware/
 ```

 2. Build the docker container:

 ```shell
 docker compose up --build -d
 ```
 3. (optional) If you want to use GUI apps inside the docker container run this. When running things remotely using ssh this needs to be ran on the local system before ssh connection is established.

 ```shell
 xhost +local:docker
 ```

 4. Connect with a shell:

 ```shell
 docker compose exec ros2_dev /bin/bash
 ```

 ### **Starting main ros package**
 1. Follow Docker startup instructions.

 2. Inside the container run:

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
> **Note:** ros2 topic hz takes a few moments to calculate the frequency of data, don't expect instantaneous result. For high data size and frequency the actual Hz value might be wrong, you just want to see something coming through.

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
 The MS-01 NUC is set to accept SSH traffic on the default port. Connection details can be found physically on the machine. If a display is required, add the `-X` flag before `username@ip`. Won't go into details how this is setup but it's just a ssh server setup.

 For ease of development, local changes can be pushed to the NUC using `./firmware/sync_to_nuc.sh`. This allows changes made on the local system to be pushed to the NUC without going through GitHub.
 
 This script should only be used during development and for quick tests. **Working, finalized code should always be manually committed and pulled to the NUC.** Before pulling on the NUC, run `git restore .` to revert to the latest published version.

 ### **Basler cameras**
 Pylonviewer works like normal inside the container. For ros2 handling of the basler cameras one can use `ros2 launch pylon_ros2_camera_wrapper pylon_ros2_camera.launch.py camera_id:="Basler_{pos}" config_file:="/ros2_ws/config/basler_{pos}.yaml"` although this doesn't do much as a standalone node setup.
 
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
 
### **STATUS PAGE**

 The status page provides a web interface for controlling data collection and monitoring sensor health. Sensor health is read through the standard ROS 2 diagnostics pipeline:

```text
sensor diagnostic publishers -> /diagnostics -> diagnostic_aggregator -> /diagnostics_agg -> web UI
```

 The page shows a traffic-light sensor summary. The traffic-light table displays:

- Sensor status: green/yellow/red/black indicator
- Sensor name
- Final health level
- Measured Hz compared against the expected Hz for that sensor type
- PTP status for cameras and lidars, when exposed by diagnostics

 The final health level is based on the worse result between the ROS diagnostic level and the manual Hz check. IMU and GNSS do not use the PTP column.

 The web page can be ran manually with:

 1. Create and activate a Python virtual environment:

 ```shell
 python3 -m venv .venv
 source .venv/bin/activate
 ```

 2. Install dependencies:

 ```shell
 pip install -r src/requirements.txt
 ```

 3. Start the ROS 2 diagnostic aggregator:

 ```shell
 ros2 run diagnostic_aggregator aggregator_node \
   --ros-args \
   --params-file diagnostic_aggregator.yaml
 ```

 The aggregator config should use `analyzers` as the top-level node name and publish aggregated diagnostics on `/diagnostics_agg`. The web UI subscribes to `/diagnostics_agg`; individual sensor nodes should publish raw diagnostics to `/diagnostics` (if implemented in the driver).

 4. Launch the web server from a ROS-sourced terminal:

 ```shell
 source /opt/ros/$ROS_DISTRO/setup.bash
 source install/setup.bash
 python3 -m uvicorn src.webUI.app:app --host 0.0.0.0 --port 8080
 ```

 5. Allow the port on the firewall if accessing remotely:

 ```shell
 sudo iptables -I INPUT 5 -p tcp --dport 8080 -j ACCEPT
 ```

 6. Open a browser and navigate to:

 ```text
 http://localhost:8080
 ```

 or replace `localhost` with the host machine's IP address if accessing remotely.

 7. Use the **Start Collecting Data** and **Stop Collecting Data** buttons to control data collection.

 > **Note:** These buttons call the ROS 2 service `/set_data_collection_enabled`. The service must be running before the web interface can control data collection.

 8. Verify that the diagnostics pipeline is running:

 ```shell
 ros2 topic echo /diagnostics --once
 ros2 topic echo /diagnostics_agg --once
 curl http://localhost:8080/diagnostics
 ```

 Useful troubleshooting commands include:

 ```shell
 ros2 node list
 ros2 topic list
 ros2 topic hz <topic_name>
 ros2 service list | grep set_data_collection_enabled
 ```

 Expected ROS nodes during testing include:

 ```text
 /diagnostic_test_publisher
 /analyzers
 /web_ui_node
 ```

 Fake diagnostic data can be sent for testing by running the web UI test publisher:

 ```shell
 python3 src/webUI/webUI_test.py
 ```

 The test publisher sends sample diagnostics to `/diagnostics`; the diagnostic aggregator converts them to `/diagnostics_agg`, which the web UI reads.
