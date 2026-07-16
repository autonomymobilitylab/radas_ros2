# Calibration

## Intrinsic Calibraton

## Extrinsic Calibration
For extrinsic calibration, this project uses the FraunhoferIOSB [multisensor calibration toolbox](https://github.com/FraunhoferIOSB/multisensor_calibration) with a custom shell script ```launch_extrinsic_calibration.sh``` and a custom calibration target. 

### Launch and usage
The custom shell script ```launch_extrinsic_calibration.sh``` queries the user on the preferred calibration type:
```shell
Select calibration type:
1) LIDAR-to-LIDAR
2) LIDAR-to-Camera
Enter 1 or 2: 
```
Both calibration types use the hemispherical LIDAR XT32 as their reference. 
#### 1): LIDAR-to-LIDAR
After selecting 1, the extrinsic calibration toolbox will launch a GUI with 4 windows (from left-to-right, up-to-down):
1. A control window displaying calibration progress and console logs.
2. A window displaying calibration target placement guidance. **THIS FEATURE IS NOT FULLY DEVELOPED YET, DON'T USE IT**.
3. Target LIDAR view.
4. Source LIDAR view.

Once the toolbox has booted and you can see live feed from both LIDARS, place the calibration target in view of both LIDARS so that it's highlighted. 
From here, press **Capture Target Observation**. After this, the target will be highlighted in yellow with different colors of dots marking the corners of the AruCo-targets. Ensure that this highlighting is identical between the two lidars. If not, press **Remove Last Observation**.
#### 2) LIDAR-to-Camera:
After selecting 2, the shell script will promp the user to choose camera position to calibrate:
```shell
Choose camera to calibrate ['left', 'middle', 'right']: 
```
Enter your preferred camera and press enter. After this the toolbox will launch the calibration GUI. Different from LIDAR-to-LIDAR calibration is that the calibration target placement guidance on the upper right corner of the screen actually works. Follow its instructions on target placement. 

Once the target is in place, press **Capture Target Observation**. If the corners between the LIDAR and camera view don't match, press **Remove Last Observation** and repeat the process.

Continue this process for atleast 5 different observations, holding the target in a different orientation, different position of the LIDAR's/Camera's FOV. If the toolbox gets stuck after capturing target observation, try moving around to a new location with the target. If this doesn't resolve after a while, kill the process and start again. 

After enough suitable target observations, press **Calibrate**. This will print out the calibration results to the console, but this is also saved to the location ```firmware/config/last_observation.yaml``` (for LIDARs) or ```firmware/config/extrinsics/[camera_pos]``` (for cameras). 

**Inspecting calibration results**


### Custom calibration target 
The calibration target is configured and defined with the following files:
```
Radas_calibration_target_cloud_3hole.ply
Radas_calibration_target_mesh_3hole.ply
TargetWithCirclesAndAruco.yaml
```
All of these files are located in the folder ```firmware/config```

To configure the toolbox to use a different calibration target, follow [these](https://fraunhoferiosb.github.io/multisensor_calibration/calibration_target/#using-a-custom-calibration-target) instructions from the calibration toolbox documentation. In addition to the ```.yaml``` configuration file, you have to adapt the target cloud and mesh in cad to match the used target. 