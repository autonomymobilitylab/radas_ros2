# Calibration

## Intrinsic Calibraton

## Extrinsic Calibration
For extrinsic calibration, this project uses the FraunhoferIOSB [multisensor calibration toolbox](https://github.com/FraunhoferIOSB/multisensor_calibration) with a custom shell script ```launch_extrinsic_calibration.sh``` and a custom calibration target. 

### Launch and usage


### Custom calibration target 
The calibration target is configured and defined with the following files:
```
Radas_calibration_target_cloud.ply
Radas_calibration_target_mesh.ply
TargetWithCirclesAndAruco.yaml
```
To configure the toolbox to use a different calibration target, follow [these](https://fraunhoferiosb.github.io/multisensor_calibration/calibration_target/#using-a-custom-calibration-target) instructions from the calibration toolbox documentation. In addition to the ```.yaml``` configuration file, you have to adapt the target cloud and mesh to match the used target. 