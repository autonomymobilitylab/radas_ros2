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

### Custom calibration target 
The calibration target is configured and defined with the following files:
```
Radas_calibration_target_cloud.ply
Radas_calibration_target_mesh.ply
TargetWithCirclesAndAruco.yaml
```
All of these files are located in the folder ```firmware/config```

To configure the toolbox to use a different calibration target, follow [these](https://fraunhoferiosb.github.io/multisensor_calibration/calibration_target/#using-a-custom-calibration-target) instructions from the calibration toolbox documentation. In addition to the ```.yaml``` configuration file, you have to adapt the target cloud and mesh in cad to match the used target. 