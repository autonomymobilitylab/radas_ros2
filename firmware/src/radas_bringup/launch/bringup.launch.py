from launch import LaunchDescription
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    """diagnostic_config_file = os.path.join(
        get_package_share_directory('radas'),
        'config',
        'diagnostic_aggregator.yaml'
    )"""

    # ws_dir = "/ros2_ws"
    # web_ui = ExecuteProcess(
    #    cmd=[
    #        os.path.join(ws_dir, ".venv", "bin", "python3"),
    #        "-m",
    #        "uvicorn",
    #        "src.webUI.app:app",
    #        "--host",
    #        "0.0.0.0",
    #        "--port",
    #        "8080",
    #    ],
    #    cwd=ws_dir,
    #    output="screen",
    # )

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
        # Node(
        #    package="diagnostic_aggregator",
        #    executable="aggregator_node",
        #    name="analyzers",
        #    output="screen",
        #    parameters=[
        #        os.path.join(ws_dir, "diagnostic_aggregator.yaml")
        #    ],
        # )
        # web_ui,
    ]
    return LaunchDescription(nodes)
