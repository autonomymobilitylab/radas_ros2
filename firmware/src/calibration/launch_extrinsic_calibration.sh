#!/bin/bash
printf "Select calibration type:\n  1) LIDAR-to-LIDAR\n  2) LIDAR-to-Camera\n"
read -r -p "Enter 1 or 2: " CALIB_TYPE

ros2 run multisensor_calibration initialize_robot_workspace --ros-args -p robot_ws_path:="/calib_ws" -p robot_name:="calibration"

case $CALIB_TYPE in
    1)
        ros2 run multisensor_calibration extrinsic_lidar_lidar_calibration \
            --ros-args \
            robot_ws_path        :="/calib_ws" \
            target_config_file   :="/ros2_ws/config/TargetWithCirclesAndAruco.yaml" \
            src_lidar_sensor_name:="hesai_lidar_xt" \ 
            src_lidar_cloud_topic:="/lidar_points_xt" \
            ref_lidar_sensor_name:="hesai_lidar_jt" \
            ref_lidar_cloud_topic:="/lidar_points_jt"
        ;;
    2)
        CAMERA_NAME=""
        CAMERA_ID=""
        while :; do
            read -r -p "Choose camera to calibrate ['left', 'middle', 'right']: " CAMERA_POS 
            case "$CAMERA_POS" in
                left)
                    CAMERA_NAME="Basler_left"
                    CAMERA_ID="camera_left"
                    break
                    ;;
                middle)
                    CAMERA_NAME="Basler_middle"
                    CAMERA_ID="camera_middle"
                    break
                    ;;
                right)
                    CAMERA_NAME="Basler_right"
                    CAMERA_ID="camera_right"
                    break
                    ;;
                *) 
                    echo "Please enter valid camera pos: ['left', 'middle', 'right']"
                    ;;
            esac
        done

    ros2 run multisensor_calibration extrinsic_camera_lidar_calibration \
        --ros-args \
        robot_ws_path:="ros2_ws" \
        target_config_file:="/ros2_ws/config/TargetWithCirclesAndAruco.yaml" \
        camera_sensor_name:="$CAMERA_ID" \
        camera_image_topic:="/$CAMERA_NAME/pylon_ros2_camera_node/image_raw" \
        lidar_sensor_name:="hesai_lidar_xt" \
        lidar_cloud_topic:="/lidar_points_jt"
    ;;

  *)
    echo "Invalid selection; please run again and enter 1 or 2." >&2
    exit 1
    ;;
esac
