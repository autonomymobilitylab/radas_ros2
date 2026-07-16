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
        RESULT_DST=""
        RESULT_SRC=""
        while :; do
            read -r -p "Choose camera to calibrate ['left', 'middle', 'right']: " CAMERA_POS 
            case "$CAMERA_POS" in
                left)
                    CAMERA_NAME="Basler_left"
                    CAMERA_ID="camera_left"
                    RESULT_SRC="/calib_ws/camera_left_xt32_extrinsic_calibration/calibration_results.txt"
                    RESULT_DST="/ros2_ws/config/extrinsics/left/last_left_calib.yaml"
                    break
                    ;;
                middle)
                    CAMERA_NAME="Basler_middle"
                    CAMERA_ID="camera_middle"
                    RESULT_SRC="/calib_ws/camera_middle_xt32_extrinsic_calibration/calibration_results.txt"
                    RESULT_DST="/ros2_ws/config/extrinsics/middle/last_middle_calib.yaml"
                    break
                    ;;
                right)
                    CAMERA_NAME="Basler_right"
                    CAMERA_ID="camera_right"
                    RESULT_SRC="/calib_ws/camera_right_xt32_extrinsic_calibration/calibration_results.txt"
                    RESULT_DST="/ros2_ws/config/extrinsics/right/last_right_calib.yaml"
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
        -p camera_image_topic:="/$CAMERA_NAME/pylon_ros2_camera_node/image_rect" \
        -p camera_info_topic:="/$CAMERA_NAME/pylon_ros2_camera_node/camera_info" \
        -p image_state:="UNDISTORTED" \
        -p lidar_sensor_name:="xt32" \
        -p lidar_cloud_topic:="/lidar_points_xt" \
        -p use_initial_guess:=false

        CALIB_PID=$!
        wait "$CALIB_PID"

        if [ -f "$RESULT_SRC" ]; then
            cp "$RESULT_SRC" "$RESULT_DST"

            echo "Copied calibration result:"
            echo "  from: $RESULT_SRC"
            echo "  to:   $RESULT_DST"
        else
            echo "ERROR: Calibration result file was not found:"
            echo "  $RESULT_SRC"
            exit 1
        fi
        ;;
  *)
    echo "Invalid selection; please run again and enter 1 or 2." >&2
    exit 1
    ;;
esac
