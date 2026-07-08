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
     
    nodes = [
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
        hemi_data_collection,
        dome_data_collection
    ]
    return LaunchDescription(nodes)
