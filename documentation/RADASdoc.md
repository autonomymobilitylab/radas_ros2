___
# RADAS user manual
This document is intended for the future use and development of the RADAS sensor rack by new users. This document is intended to fill the gaps left by the project README by serving as a general document on RADAS rather than a short bulletpoint list of setup steps. 

___
# Overview
The Rugged ATV Data Acquisition System (or RADAS) is a modular, plug-and-play sensor solution intended for capturing data in unstructured, forested areas. The purpose of this document is to provide a new user of the system with the expertise and know-how to initialize, operate and troubleshoot the system. 

The system is comprised of a central PC/NUC, 6 ethernet devices connected via a switch and 3 USB-devices. The devices used are:

| Device name                  | Device type          | Connection to NUC |
| ---------------------------- | -------------------- | ----------------- |
| Ubiquiti UniFi Flex 2.5G PoE | Switch               | SFP               |
| Basler a2A1920-51gcBAS       | RGB Camera           | RJ45              |
| Basler a2A1920-51gcBAS       | RGB Camera           | RJ45              |
| Basler a2A1920-51gcBAS       | RGB Camera           | RJ45              |
| Hesai XT32M2X                | Hemispherical LIDAR  | RJ45              |
| Hesai JT128                  | Dome LIDAR           | RJ45              |
| Xsens MTi-320-3A-SK          | IMU                  | USB               |
| FTDI UM232H                  | USB to GPIO breakout | USB               |
| Ardusimple SimpleRTK4 H      | RTK GNSS-module      | USB               |

___
# Usage
### Powering the system
==TODO:== Attach pictures to all the steps described/of the full electrical connection diagram
The sensor rack only has 2 required connections to function: DC + and DC -. Powering the sensor rack happens via a DC input source, which can be a bench supply or an automotive auxiliary socket for example. The system accepts **12 V** at **20 A max**. 
>**Note:** the sensor rack browns out at around 9 V. As a result, it's critical that your DC source is stable and not susceptible to fluctuations. 

> **Note:** It is possible to power all the main components via their original AC adapters in troubleshooting scenarios. These AC adapters are not attached to the system, but they can be found at the lab instead. Doing this will bypass most of the elements, such as main power switch, power indicator lights and fusing described below

After the power has been connected, turn the main power switch from the position **OFF** to **ON** ==PICTURE HERE==

The system being powered should be indicated by the main power led turning on ==PICTURE HERE==

> **Troubleshoot:** If the main power led does not turn on or the rest of the system lacks all signs of life (LIDARs aren't audibly spinning, status led remains off) , check the main 20 A fuse inside the electrical cabinet. If it's blown, replace it. In other cases, check your power supply and finally change to powering the system via the AC adapters. 
### Recording via the provided Web UI
The ROS2 rosbag functionality is used to implement sensor output data recording. The recording is controlled via the Web UI with the labeled buttons on top of the page. Functionality is dead simple:
1. **```Start recording```** initializes a new rosbag and starts recording output data to a rosbag named ```system_recording_dd-mm-yy_hh-mm-ss``` which results in a uniquely named output rosbag based on recording time.
2. **```Pause recording```** pauses current recording, but does not finalize or close the current rosbag.
3. **```Resume recording```** continues paused recording to the same rosbag initialized with the last Start recording-command.
4. **```Stop recording```** stops the recording and finalizes and closes the current rosbag. After this, recording to the same rosbag is not possible and a new rosbag needs to be initialized via Start recording. 

Output data location on the NUC is **```/home/amlab/radas_ros2/firmware/output_data/rosbags```**
### Connecting to the system using a shell

### Finalizing the recording and turning off the system
Ending and closing the recording happens via pressing the **```Stop recording```** button in the Web UI. This safely finalizes and closes the current rosbag, after which the system can simply be powered off via flipping the main power switch. 


In case of a sudden shutdown of the system, the ROS 2 implementation of rosbag, the recording will still work due to using the MCAP-storage plugin, but all buffered frames will be lost, this will equal to around 5 frames. Reading the MCAP bag after an unexpected shutdown does require an external tool (not yet tested/covered). 
### Viewing and accessing the output data
Output data location on the NUC is **```/home/amlab/radas_ros2/firmware/output_data/rosbags```**
___
# Calibration
Calibration is an important step of in the operation of the system, but it isn't listed in the usage section as the sensor rack calibration has to be repeated only when the system changes: components are replaced or their positions are moved relative to each other. 

For both types of calibration, you will need the specific kind of calibration target suitable for the type of calibration. Both targets can be found at the garage.
### Intrinsic calibration
- Calibration target: checkerboard pattern target
==PICTURE OF TARGET==
Intrinsic calibration is used to determine the focal length, principal points and lens distortion of the cameras. Knowing these values, we can correct the lens distortion introduced especially by wide-FOV lenses to achieve a flatter, rectified image. 
### Extrinsic calibration
- Calibration target: target with ArUco Markers and 3 circular cutouts
==PICTURE OF TARGET==

Extrinsic calibration is used to determine the translation and rotation matrices between the "root" sensor (XT32 LIDAR) and one of the 4 remaining sensors (JT128 LIDAR or Basler RGB cameras). Knowing these translation and rotation matrices between the sensors enables us to overlap and align their data ==PICTURE OF THE ALIGNED FRAMES==. 
>**Note:** You can use the big CTOUCH-screen located at the garage to have an easier time viewing your target positioning
___
# Software and operation overview
### Docker
Docker containerization is used 

### ROS 2

### Sensor triggering and synchronization
- **Sensor clock source:**
The most fundamental aspect of data frame alignment and sensor synchronization is the synchronization of their internal clocks used for timestamping each frame. To achieve this, RADAS uses the IEEE 1588-standard **Precision Time Protocol** (later PTP). The main PC/NUC of the system serves as the PTP-GM, the main clock which is used to serve time to other devices. We use hardware timestamping, because the NUC features a built-in network interface card supporting the protocol. Not being connected to UTC-time is not a problem, because the local PC time is the same for all sensors after slaving them to the PC.
- **Slaving sensors to the PTP-GM**
PTP's delay requests and responses, used for controlling the slave clock, can natively be transmitted only over ethernet, and thus it's served only to our ethernet-connected devices. The system's cameras are configured to enable PTP as their clock source during our driver launch, while the LIDARS are configured to use PTP through the lidarutilities-software/manufacturer web UI. ==EXPAND THIS, WITH PICTURES FOR EXAMPLE==
- **Camera trigger source**
We utilize the camera's ability to receive external hardware trigger signals. This signal is provided by the Ardusimple GNSS-module. To configure this signal, it's possible to use the manufacturer's RxControl-software under ==INSERT PATH HERE==. 
___
# Troubleshooting
### Viewing container/ROS 2 logs 

### Using the manufacturer device software
- **RGB-Cameras: Basler PylonVIewer**

- **LIDARS: Hesai Lidautilities, webUI and Pandarview**

- **GPS: RxControl**

### Not receiving data from LIDARS

### Not receiving data from cameras

### Not receiving data from IMU/GPS
___
# Misc
### Adding new or replacing old components

The current sensor rack system is very modular. The aluminium profile assembly allows easy modification of the current structure with the software being modular through the containerization of the software.  There are a few important points for adding new components to the current system. These include accessing the device and device drivers.

- **Accessing the device**
For ethernet-connected devices, it's important that the data-packets sent by the device are not blocked by the NUC firewall. on our NUC, ```sudo iptables -F``` can be used to temporarily allow data-packets to arrive at the PC, but it is advisable to find out to which port the new sensor sends data and permanently allow that port through in your firewall rules. The iptable-rules can reset upon network connection reset, such as disconnecting and reconnecting the device.

USB devices have 1 similar detail to look out for. The device might belong to a specific user group, and if your user is not a part of it, you will not be able to access or use the devices. For example the IMU and GPS-modules both belong to the ```dialout```-group, and you have to modify your user's access rights to be able to use these devices. This modification has already been implemented on the system's NUC, but future devices could use different groups. 

- **Device drivers**
There is 1 simple test you can do before even buying a new device for the system. Add the new device drivers to the current Dockerfile and attempt to build the container. The build being successful is not a full guarantee of the sensor compatibility, but the build failing is a sure indicator that the drivers have to be figured out before purchasing said part.
___
