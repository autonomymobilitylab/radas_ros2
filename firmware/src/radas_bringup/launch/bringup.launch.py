from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, TimerAction

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    ptp_configurator = TimerAction(
        period=5.0,
        actions=[
            Node(
                package="basler_ptp_config",
                executable="basler_ptp_configurator",
                name="basler_ptp_configurator",
                output="screen",
            )
        ]
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

    hardware_trigger_configurator = ExecuteProcess(
        cmd=[
            "/ros2_ws/src/.venv/bin/python3",
            "/ros2_ws/src/cameras/hardware_trigger.py",
        ],
        cwd="/ros2_ws",
        output="screen",
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
        hardware_trigger_configurator,
        #ptp_configurator,
    ]
    return LaunchDescription(nodes)
