from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    hemi_data_collection = ExecuteProcess(
        cmd=[
            "/ros2_ws/src/.venv/bin/python3",
            "/ros2_ws/src/lidars/lidarnode.py",
            "--lidar-name=xt",
        ],
        cwd="/ros2_ws",
    )

    dome_data_collection = ExecuteProcess(
        cmd=[
            "/ros2_ws/src/.venv/bin/python3",
            "/ros2_ws/src/lidars/lidarnode.py",
            "--lidar-name=jt",
        ],
        cwd="/ros2_ws",
    )

    left_data_collection = ExecuteProcess(
        cmd=[
            "/ros2_ws/src/.venv/bin/python3",
            "/ros2_ws/src/cameras/cameranode.py",
            "--camera-name=Basler_left",
        ],
        cwd="/ros2_ws",
    )
    middle_data_collection = ExecuteProcess(
        cmd=[
            "/ros2_ws/src/.venv/bin/python3",
            "/ros2_ws/src/cameras/cameranode.py",
            "--camera-name=Basler_middle",
        ],
        cwd="/ros2_ws",
    )
    right_data_collection = ExecuteProcess(
        cmd=[
            "/ros2_ws/src/.venv/bin/python3",
            "/ros2_ws/src/cameras/cameranode.py",
            "--camera-name=Basler_right",
        ],
        cwd="/ros2_ws",
    )

    nodes = [
        Node(
            namespace="Basler_left",
            package="pylon_ros2_camera_wrapper",
            executable="pylon_ros2_camera_wrapper",
            name="pylon_ros2_camera_node",
            output="screen",
            emulate_tty=True,
            parameters=[
                "/ros2_ws/config/basler_left.yaml",
                {
                    "startup_user_set": "CurrentSetting",
                    "enable_status_publisher": False,
                    "enable_current_params_publisher": False,
                },
            ],
        ),
        Node(
            namespace="Basler_middle",
            package="pylon_ros2_camera_wrapper",
            executable="pylon_ros2_camera_wrapper",
            name="pylon_ros2_camera_node",
            output="screen",
            emulate_tty=True,
            parameters=[
                "/ros2_ws/config/basler_middle.yaml",
                {
                    "startup_user_set": "CurrentSetting",
                    "enable_status_publisher": False,
                    "enable_current_params_publisher": False,
                },
            ],
        ),
        Node(
            namespace="Basler_right",
            package="pylon_ros2_camera_wrapper",
            executable="pylon_ros2_camera_wrapper",
            name="pylon_ros2_camera_node",
            output="screen",
            emulate_tty=True,
            parameters=[
                "/ros2_ws/config/basler_right.yaml",
                {
                    "startup_user_set": "CurrentSetting",
                    "enable_status_publisher": True,
                    "enable_current_params_publisher": False,
                },
            ],
        ),
        Node(
            namespace="radas_xt",
            package="hesai_ros_driver",
            executable="hesai_ros_driver_node",
            name="xt32",
            output="screen",
            parameters=[
                {
                    "config_path": os.path.join(
                        get_package_share_directory("radas_bringup"),
                        "config",
                        "xt32.yaml",
                    )
                }
            ],
        ),
        Node(
            namespace="radas_jt",
            package="hesai_ros_driver",
            executable="hesai_ros_driver_node",
            name="jt128",
            output="screen",
            parameters=[
                {
                    "config_path": os.path.join(
                        get_package_share_directory("radas_bringup"),
                        "config",
                        "jt128.yaml",
                    )
                }
            ],
        ),
        Node(
            package="jt_correction",
            executable="jt_pointcloud_corrector",
            name="jt_pointcloud_corrector",
            output="screen",
            parameters=["/ros2_ws/config/jt_calibration.yaml"],
            remappings=[
                ("input", "/lidar_points_jt"),
            ],
        ),
        hemi_data_collection,
        dome_data_collection,
        left_data_collection,
        middle_data_collection,
        right_data_collection,
    ]
    return LaunchDescription(nodes)
