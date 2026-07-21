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
            package="septentrio_gnss_driver",
            executable="septentrio_gnss_driver_node",
            name="gnss_rover",
            namespace="Gnss",
            output="screen",
            emulate_tty=True,
            sigterm_timeout="20",
            parameters=[
                "/opt/ros/jazzy/share/septentrio_gnss_driver/config/custom_rover.yaml"
            ],
        ),
        hemi_data_collection,
        dome_data_collection,
        left_data_collection,
        middle_data_collection,
        right_data_collection,
    ]
    return LaunchDescription(nodes)
