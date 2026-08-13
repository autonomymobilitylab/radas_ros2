# Rugged ATV Data Acquisition System (RADAS)

### **Collaborators:**

 - [Aalto University Autonomy & Mobility Lab](https://www.aalto.fi/en/department-of-energy-and-mechanical-engineering/autonomy-mobility-lab): Joel Ventola, Otto Peltonen

# Overview

The Rugged ATV Data Acquisition System, or RADAS, is a versatile, rugged sensor rack designed to be mounted on the front cargo area of an ATV. With its modular design and small footprint, the system can also be mounted on other vehicles and platforms.

The purpose of this system is to collect real-world data for state-of-the-art (SOTA) datasets in unstructured off-road environments, such as forests and other off-road areas in Finland.

The system includes two different LiDAR sensors, three RGB cameras that provide a 170° field of view, a 9-DoF IMU, and an RTK-capable GNSS receiver. The system is also planned to be upgraded with an additional NIR (near-infrared) camera in the future.
The sensors and their specifications are listed in more detail in the table below.

### **Sensors**
 - 32-channel 360° LiDAR: [Hesai XT32M2X](https://www.hesaitech.com/product/xt16-32-32m/)
 - 128-channel dome LiDAR: [Hesai JT128](https://www.hesaitech.com/product/jt128/)
 - 3 x RGB-cameras: [Basler a2A1920-51gcBAS](https://www.baslerweb.com/en/shop/a2a1920-51gcbas/)
 - IMU: [Xsens MTi-320-3A-SK](https://www.xsens.com/sensor-modules/xsens-mti-320)
 - RTK-GNSS: [Ardusimple simpleRTK 4 Heading](https://www.ardusimple.com/product/simplertk-4-heading/)

# Guide
This guide contains information about many of the tools and procedures used during development. It does not necessarily reflect the final deployed system.

## **Prerequisites**

### **Software**
- [Ubuntu 24.04 LTS (Noble Numbat)](https://releases.ubuntu.com/noble/)
- [Docker 29.5.2, build 79eb04c](https://github.com/docker/docker-install)

### **Hardware**
- NUC/PC with adequite processing power, ram and storage space
- Network switch with 10GigE upstream and POE functionality
- Sensors listed in above table
- USB gpio breakout board and RGB led
- Power switch and power indicator led
- IP rated enclosure for electronics
- 12 to X volt converters for power
- Router for wireless access to the lan network
- Fusebox

## **Installation**
 1. Make sure you have the prerequisites listed above installed.

 2. Clone the repository and navigate to the `firmware` directory:

 ```shell
 git clone https://github.com/joevento/radas_ros2.git
 cd ./radas_ros2/firmware
 ```

 3. Create an .env with the following keys:
 ```text
 PROJECT_DIR=/full/path/to/radas_ros2/firmware/folder
 SERVICE_USER=user account to be used for systemctl
 PTP_INTERFACE=network interface for ptp
 NTRIPUSER=ntrip clients username (in finland use maanmittauslaitos username)
 NTRIPPASS=ntrip clients password (in finland use maanmittauslaitos password)
 ```

 4. Configure the NUC's network interface with the following static network settings:

    * **IP address:** `192.168.1.2`
    * **Subnet mask:** `255.255.255.0`

 5. Manually start the container to make sure everything works as intended:

 ```shell
 docker compose up --build
 ```

 6. Once the container has started successfully, navigate to `http://localhost:8080/` (or `http://192.168.1.2:8080/` when remote) to access the system's web interface. Each sensor is displayed in its own table, with a traffic light indicator in the first column showing its general status. Verify that all sensors show a green status.

 7. Once the system's functionality has been verified, stop the container using `Ctrl+C`.

 8. **(Optional)** Create an unprivileged user account under which the system will run.

 9. Regardless of whether you completed the optional step above, make sure the account used to run the system is automatically logged in at startup. This prevents the NUC from getting stuck on the login screen when the system is powered on.

    Automatic login can be enabled in the Ubuntu settings under:

    `System -> Users -> Automatic Login`

 > **Note:** If the Users page is grayed out, click the **"Unlock..."** button in the top-right corner.

 10. Once the functionality of the system has been verified manually, run the systemd service installation script from the `firmware` directory:

 ```shell
 ./install_service.sh
 ```

 The script installs and enables the systemd service responsible for starting the RADAS ROS 2 system automatically when the user logs in.

 11. Once the service has been installed successfully, restart the NUC and enter the BIOS (typically by pressing `F2` or `Del`). In the BIOS, enable automatic startup when power is restored.

     On the MS-01, this setting can be found under:

     `Advanced -> ACPI -> Restore Power on AC Power Loss`

     This ensures that the NUC boots and subsequently logs in automatically when the main power switch is turned on.

 12. Save the BIOS settings and exit. Allow the system to boot into Ubuntu, then navigate to `http://localhost:8080/` (or `http://192.168.1.2:8080/` when accessing remotely) and verify that all sensor status indicators are green.

 13. The system is now ready for use. From this point onward, it will automatically boot, log in, and start the RADAS ROS 2 system when the power switch on the side of the electrical cabinet is turned on.

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

 1. Navigate to the `firmware` subdirectory:

 ```shell
 cd ./firmware/
 ```

 2. Build and start the Docker container in the background:

 ```shell
 docker compose up --build -d
 ```

 3. **(Optional)** To use GUI applications from inside the Docker container, allow local Docker containers to connect to the X server:

 ```shell
 xhost +local:docker
 ```

 > **Note:** When connecting to the system remotely via SSH, this command must be run on the local computer (e.g. laptop) before establishing the SSH connection.

 4. Open a shell inside the running container:

 ```shell
 docker compose exec ros2_dev /bin/bash
 ```

 ### **Starting the Main ROS 2 Package**

 1. Follow the Docker startup instructions above and open a shell inside the container.

 2. Inside the container, run:

 ```shell
 ros2 launch radas_bringup bringup.launch.py
 ```

 This launches the main RADAS ROS 2 bringup package.

 ### **LiDARs**

 #### **PandarView2**

 1. Make sure the device firewall is disabled or that the LiDAR UDP port (typically `2368`) is allowed through the firewall:

 ```shell
 sudo ufw disable
 sudo iptables -F
 ```

 > **Note:** Disconnecting and reconnecting the LiDAR may result in the firewall rules being reset, after which the port must be allowed through again.

 2. Check the IP address of the wired network interface:

 ```shell
 ip -br addr
 ```

 > **Note:** For troubleshooting or sanity-checking, you can verify that the connected LiDAR is sending UDP data using:
 >
 > `sudo tcpdump -i <NIC_device_name> -n udp port 2368`
 >
 > Alternatively, use Wireshark to inspect the network traffic.

 3. The default IP address of Hesai LiDARs is `192.168.1.201`. For models that support a web interface, navigate to this address in a browser to view and configure the LiDAR parameters.

    Models that do not support the web interface, such as the JT128, require Hesai's LidarUtilities software to view and modify their parameters.

 4. Launch PandarView2 and select `Listen for Data` (or press `Ctrl+R`). The host IP can either be set to `Any` or to the IP address of the wired network interface connected to the LiDAR.

 5. Once data is being received, import the corresponding angle correction file.

 #### **ROS 2 and RViz2**

 Use the same network configuration described in the PandarView2 section above.

 This guide does not cover creating the workspace, cloning the manufacturer's drivers/SDK, or installing ROS 2 package dependencies. Instead, it covers the most important configuration file changes required for the LiDARs.

 1. Configure the IP addresses in the LiDAR configuration file:

    - Set the **device IP address** to the address configured on the LiDAR.
    - Set the **host IP address** to the address of the wired network interface connected to the LiDAR.
    - Replace the **multicast IP address** with an empty string (`""`).

    All IP addresses should be specified as strings in the following format:

    ```text
    "192.168.1.xxx"
    ```

 2. Clear the following placeholder paths:

 ```yaml
 firetimes_path: ""
 ***
 channel_fov_filter_path: ""
 multi_fov_filter_ranges: ""
 ```

 3. Download the appropriate correction file for the LiDAR and configure its path. For example:

 ```yaml
 correction_file_path: "/home/user/hesai_ws/config/jt128_correction.csv"
 ```

 4. Make sure the required data is published through ROS 2:

 ```yaml
 ros:
    ros_frame_id: hesai_lidar
    ***
    send_packet_ros: true
    send_point_cloud_ros: true
    send_imu_ros: true
 ```

 5. Check the configured frame frequency. If it is set to `0`, change it to an appropriate value. For example:

 ```yaml
 frame_frequency: 10
 default_frame_frequency: 10.0
 ```

 6. Launch the LiDAR node and RViz2. To verify that the ROS 2 topics are available, run:

 ```shell
 ros2 topic list
 ```

 You should see LiDAR-related topics such as `/lidar_points`.

 Check the topic information and publishing frequency with:

 ```shell
 ros2 topic info /lidar_points
 ros2 topic hz /lidar_points
 ```

 `ros2 topic info /lidar_points` should return something similar to:

 ```text
 Type: sensor_msgs/msg/PointCloud2
 Publisher count: 1
 Subscription count: 0
 ```

 If `ros2 topic hz /lidar_points` does not return any data, ROS 2 is likely not receiving the LiDAR data stream.

 > **Note:** `ros2 topic hz` takes a few moments to calculate the publishing frequency, so do not expect an instantaneous result. With high data rates or large messages, the reported frequency may also be inaccurate. For troubleshooting purposes, the important thing is to verify that data is being received.

 ### **PTP**

 #### **Setting Up the NUC as a PTP Grandmaster**

 PTP is automatically configured when running:

 ```shell
 docker compose up --build -d
 ```

 The PTP service runs in a secondary container alongside the main ROS 2 container.

 To manually broadcast PTP from the device, for example for testing or troubleshooting, run:

 ```shell
 sudo ptp4l -i <device> -m -S
 ```

 The automatic PTP setup expects an `.env` file in the `./firmware` directory containing the network interface to use for PTP:

 ```text
 PTP_INTERFACE=<device>
 ```

 #### **LiDAR Timestamps**

 Both the JT128 and XT32M LiDARs use the same timestamp format in their data packets. The timestamp can be located manually from the raw packet data in Wireshark as follows:

 1. Starting from the end of the packet, locate the manufacturer magic value `42` in the raw Wireshark output.
 2. From `42`, move back 10 bytes (10 two-character hexadecimal byte values in Wireshark).
 3. The first byte represents `year - 1900`.
 4. The next five bytes represent, in order:
    `month, day, hour, minute, second`
 5. The final four bytes represent the microsecond component of the UTC timestamp.

 ### **SSH Access to the NUC**

 The MS-01 NUC is configured to accept SSH connections on the default SSH port. The connection details can be found physically on the machine.

 To connect to the NUC, use:

 ```shell
 ssh username@ip
 ```

 If X11 forwarding is required for graphical applications, add the `-X` option:

 ```shell
 ssh -X username@ip
 ```

 This guide does not cover the SSH server configuration itself, as the NUC uses a standard SSH server setup.

 #### **Syncing Local Changes During Development**

 For easier development, local changes can be pushed directly to the NUC using:

 ```shell
 ./firmware/sync_to_nuc.sh
 ```

 The script expects the following keys to be in your local .env file:
 ```
 REMOTE_USER=username on the nuc
 REMOTE_HOST=nuc ip address
 REMOTE_FIRMWARE_PATH=/full/path/to/radas_ros2/firmware/folder
 ```

 This allows changes made on the local development machine to be transferred to the NUC without first committing and pushing them through GitHub.

 This script should only be used during development and for quick testing. **Working, finalized code should always be committed to Git and pulled onto the NUC through the normal Git workflow.**

 Before pulling the finalized version on the NUC, discard changes previously transferred using the sync script:

 ```shell
 git restore .
 ```

 > **Warning:** `git restore .` discards uncommitted changes to tracked files. Make sure there are no changes on the NUC that need to be preserved before running this command.

 ### **Basler Cameras**

 Pylon Viewer can be used normally from inside the Docker container.

 For ROS 2 access to an individual Basler camera, the `pylon_ros2_camera_wrapper` package can be launched manually with:

 ```shell
 ros2 launch pylon_ros2_camera_wrapper pylon_ros2_camera.launch.py camera_id:="Basler_{pos}" config_file:="/ros2_ws/config/basler_{pos}.yaml"
 ```

 Replace `{pos}` with the position identifier of the camera.

 Running the camera wrapper this way is mainly useful for validating the broad functionality of the cameras inside ROS 2 and the container, as the standalone node does not provide much functionality by itself compared with the complete RADAS setup.

 ### **Running RADAS Automatically on Startup with systemd**

 The RADAS ROS 2 Docker stack can be started automatically using a systemd service.

 For this the `.env` file in the `firmware` directory should contain:

 ```shell
 PROJECT_DIR=/path/to/firmware/folder
 SERVICE_USER=localUser
 ```

 `PROJECT_DIR` should point to the RADAS `firmware` directory, and `SERVICE_USER` should be the local user account under which the system runs.

 #### **Installing the Service**

 Make the installation script executable and run it:

 ```shell
 chmod +x install_service.sh
 ./install_service.sh
 ```

 #### **Starting the Service Manually**

 ```shell
 sudo systemctl start radas_ros2.service
 ```

 #### **Viewing Logs**

 Follow the service logs in real time:

 ```shell
 journalctl -u radas_ros2.service -f
 ```

 #### **Restarting the Service**

 After making changes to the RADAS configuration or software, restart the service with:

 ```shell
 sudo systemctl restart radas_ros2.service
 ```

 #### **Disabling Automatic Startup**

 To prevent the service from starting automatically:

 ```shell
 sudo systemctl disable radas_ros2.service
 ```

 #### **Removing the Service**

 To completely remove the RADAS systemd service:

 ```shell
 sudo systemctl stop radas_ros2.service
 sudo systemctl disable radas_ros2.service
 sudo rm /etc/systemd/system/radas_ros2.service
 sudo systemctl daemon-reload
 ```

 ### **Status Page**

 The RADAS status page provides a web interface for monitoring sensor health, GNSS status, and controlling data recording.

 The page is normally started automatically as part of the RADAS Docker stack and can be accessed at:

 ```text
 http://localhost:8080
 ```

 or remotely from the RADAS network at:

 ```text
 http://192.168.1.2:8080
 ```

 #### **Diagnostics**

 Sensor health information is collected using the standard ROS 2 diagnostics pipeline:

```text
Sensor data / driver diagnostics
            |
            v
Sensor diagnostic nodes
            |
            v
      /diagnostics
            |
            v
 diagnostic_aggregator
            |
            v
    /diagnostics_agg
            |
            v
       RADAS Web UI
```

 Dedicated diagnostic nodes are used to normalize the status of the different sensor types before the information is passed to the diagnostic aggregator.

 The main sensor status table displays:

 - Traffic-light status indicator
 - Sensor name
 - Health level
 - Measured publishing frequency and expected frequency
 - Additional diagnostic details

 The traffic-light indicators represent:

 - 🟢 **Good**
 - 🟡 **Warning**
 - 🔴 **Error**
 - ⚫ **Stale / no current data**

 The expected sensor frequencies used by the status page are:

 ```text
 LiDAR:   10 Hz
 Camera:  10 Hz
 IMU:   100 Hz (fused)
 GNSS:    10 Hz
 ```

 For sensors with frequency information available, the web UI performs an additional check against the expected frequency:

 - **≥ 90%** of expected frequency: Good
 - **70–90%** of expected frequency: Warning
 - **≤ 70%** of expected frequency: Error

 The displayed health level is the more severe result of the diagnostic node's reported status and this frequency check.

 #### **Sensor Diagnostics**

 The cameras, LiDARs, IMU, and GNSS use separate diagnostic nodes.

 The **camera diagnostics** monitor the image streams of all three Basler cameras and combine their measured frame rate with the availability diagnostics produced by the Basler driver.

 The **LiDAR diagnostics** monitor the point cloud topics of both Hesai LiDARs and report their publishing frequency and stream status.

 The **IMU diagnostics** monitor the XSens IMU data stream and its publishing frequency.

 The **GNSS diagnostics** monitor the Septentrio GNSS receiver separately and provide more detailed positioning information to the web interface.

 #### **GNSS Status**

 GNSS information is displayed in a dedicated table containing:

 - Overall GNSS status
 - Positioning mode/status
 - Satellites used and visible
 - Latitude and longitude
 - Altitude
 - HDOP and PDOP
 - RF interference status
 - Spoofing status

 The GNSS diagnostic status also takes the positioning mode and availability of the required GNSS data streams into account. Detected interference or spoofing causes the GNSS diagnostic state to report an error.

 #### **System Status Indicator**

 In addition to the web interface, RADAS uses a physical status light connected through an FTDI GPIO interface.

 The light represents the overall diagnostic state of the system:

 - 🟢 **Green:** System OK
 - 🟡 **Yellow:** Warning
 - 🔴 **Red:** Error
 - 🔵 **Blue:** Diagnostics stale or unavailable

 The overall state is determined from the sensor and GNSS diagnostic states.

 #### **Recording Controls**

 The status page provides four controls for the ROS 2 system recorder:

 - **Start Recording**
 - **Pause Recording**
 - **Resume Recording**
 - **Stop Recording**

 These buttons communicate with the following ROS 2 services:

 ```text
 /system_recorder/record
 /system_recorder/pause
 /system_recorder/resume
 /system_recorder/stop
 ```

 The page also displays the current recording state and reports if a recorder request fails or the required ROS 2 service is unavailable.

 #### **Running the Status Page Manually**

 For development and testing, the web interface can be started manually.

 1. Create and activate a Python virtual environment:

 ```shell
 python3 -m venv .venv
 source .venv/bin/activate
 ```

 2. Install the required dependencies:

 ```shell
 pip install -r src/requirements.txt
 ```

 3. Make sure the ROS 2 environment and RADAS workspace are sourced:

 ```shell
 source /opt/ros/$ROS_DISTRO/setup.bash
 source install/setup.bash
 ```

 4. Start the diagnostic aggregator:

 ```shell
 ros2 run diagnostic_aggregator aggregator_node \
   --ros-args \
   --params-file diagnostic_aggregator.yaml
 ```

 5. Start the web server from another ROS-sourced terminal:

 ```shell
 python3 -m uvicorn src.webUI.app:app --host 0.0.0.0 --port 8080
 ```

 6. If accessing the web interface remotely, make sure TCP port `8080` is allowed through the firewall:

 ```shell
 sudo iptables -I INPUT 5 -p tcp --dport 8080 -j ACCEPT
 ```

 7. Open the web interface:

 ```text
 http://localhost:8080
 ```

 or, when accessing the NUC remotely:

 ```text
 http://192.168.1.2:8080
 ```

 #### **Troubleshooting**

 Check that raw diagnostics are being published:

 ```shell
 ros2 topic echo /diagnostics --once
 ```

 Check the output of the diagnostic aggregator:

 ```shell
 ros2 topic echo /diagnostics_agg --once
 ```

 The data currently received by the web UI can also be inspected directly:

 ```shell
 curl http://localhost:8080/diagnostics
 ```

 Other useful commands include:

 ```shell
 ros2 node list
 ros2 topic list
 ros2 topic hz <topic_name>
 ros2 service list
 ```
