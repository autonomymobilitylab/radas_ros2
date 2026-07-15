#!/bin/bash
printf "Select calibration type:\n  1) LIDAR-to-LIDAR\n  2) LIDAR-to-Camera\n"
read -r -p "Enter 1 or 2: " CALIB_TYPE

ros2 run multisensor_calibration initialize_robot_workspace --ros-args -p robot_ws_path:="/calib_ws" -p robot_name:="calibration"

case $CALIB_TYPE in
    1)

        ros2 run multisensor_calibration extrinsic_lidar_lidar_calibration \
            --ros-args \
            -p robot_ws_path:="/calib_ws" \
            -p target_config_file:="/ros2_ws/config/TargetWithCirclesAndAruco.yaml" \
            -p src_lidar_sensor_name:="jt128" \
            -p src_lidar_cloud_topic:="/lidar_points_jt" \
            -p ref_lidar_sensor_name:="xt32" \
            -p ref_lidar_cloud_topic:="/lidar_points_xt" \
            -p use_initial_guess:=true &

            CALIB_PID=$!

            echo "Waiting for calibration result..."
            ros2 topic echo --once \
                /extrinsic_lidar_lidar_calibration/calibration_result \
                multisensor_calibration_interface/msg/CalibrationResult \
                --filter "m.is_successful" \
                > /ros2_ws/config/last_calibration.yaml

            echo "Saved calibration result to:"
            echo "  /ros2_ws/config/last_calibration.yaml"

            wait "$CALIB_PID"
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

                    # Hesai XT -> Basler left
                    ros2 run tf2_ros static_transform_publisher \
                        0.310 0.040 0.400 \
                        0.0 0.0 0.610865 \
                        hesai_lidar_xt \
                        camera_left &
                    break
                    ;;
                middle)
                    CAMERA_NAME="Basler_middle"
                    CAMERA_ID="camera_middle"

                    # Hesai XT -> Basler middle
                    ros2 run tf2_ros static_transform_publisher \
                        0.0 0.040 0.400 \
                        0.0 0.0 0.0 \
                        hesai_lidar_xt \
                        camera_middle &
                    break
                    ;;
                right)
                    CAMERA_NAME="Basler_right"
                    CAMERA_ID="camera_right"

                    # Hesai XT -> Basler right
                    ros2 run tf2_ros static_transform_publisher \
                        -0.310 0.040 0.400 \
                        0.0 0.0 -0.610865 \
                        hesai_lidar_xt \
                        camera_right &
                    break
                    ;;
                *) 
                    echo "Please enter valid camera pos: ['left', 'middle', 'right']"
                    ;;
            esac
        done

        ros2 run multisensor_calibration extrinsic_camera_lidar_calibration \
        --ros-args \
        -p robot_ws_path:="/calib_ws" \
        -p target_config_file:="/ros2_ws/config/TargetWithCirclesAndAruco.yaml" \
        -p camera_sensor_name:="$CAMERA_ID" \
        -p camera_image_topic:="/$CAMERA_NAME/pylon_ros2_camera_node/image_raw" \
        -p camera_info_topic:="/$CAMERA_NAME/pylon_ros2_camera_node/camera_info" \
        -p lidar_sensor_name:="xt32" \
        -p lidar_cloud_topic:="/lidar_points_xt" \
        -p use_initial_guess:=true
        ;;

  *)
    echo "Invalid selection; please run again and enter 1 or 2." >&2
    exit 1
    ;;
esac
