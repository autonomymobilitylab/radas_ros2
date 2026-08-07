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
