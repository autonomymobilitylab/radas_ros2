from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    #hemi_data_collection = ExecuteProcess(
    #    cmd=[
    #        "/ros2_ws/src/.venv/bin/python3",
    #        "/ros2_ws/src/lidars/lidarnode.py",
    #        "--lidar-name=xt",
    #    ],
    #    cwd="/ros2_ws",
    #)

    #dome_data_collection = ExecuteProcess(
    #    cmd=[
    #        "/ros2_ws/src/.venv/bin/python3",
    #        "/ros2_ws/src/lidars/lidarnode.py",
    #        "--lidar-name=jt",
    #    ],
    #    cwd="/ros2_ws",
    #)

    #left_data_collection = ExecuteProcess(
    #    cmd=[
    #        "/ros2_ws/src/.venv/bin/python3",
    #        "/ros2_ws/src/cameras/cameranode.py",
    #        "--camera-name=Basler_left",
    #    ],
    #    cwd="/ros2_ws",
    #)
    #middle_data_collection = ExecuteProcess(
    #    cmd=[
    #        "/ros2_ws/src/.venv/bin/python3",
    #        "/ros2_ws/src/cameras/cameranode.py",
    #        "--camera-name=Basler_middle",
    #    ],
    #    cwd="/ros2_ws",
    #)
    #right_data_collection = ExecuteProcess(
    #    cmd=[
    #        "/ros2_ws/src/.venv/bin/python3",
    #        "/ros2_ws/src/cameras/cameranode.py",
    #        "--camera-name=Basler_right",
    #    ],
    #    cwd="/ros2_ws",
    #)
    """diagnostic_config_file = os.path.join(
       get_package_share_directory('radas'),
       'config',
       'diagnostic_aggregator.yaml'
    )"""

    ws_dir = "/ros2_ws"
    web_ui = ExecuteProcess(
        cmd=[
            "/ros2_ws/.venv/bin/python3",
            "-m",
            "uvicorn",
            "src.webUI.app:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8080",
            ],
        cwd="/ros2_ws",
        output="screen",
        )
    lidar_status = ExecuteProcess(
        cmd=[
            "/ros2_ws/.venv/bin/python3",
            "/ros2_ws/src/webUI/lidar_diagnostics.py"
            ],
        cwd="/ros2_ws",
        output="screen",
    )
    gps_status = ExecuteProcess(
        cmd=[
            "/ros2_ws/.venv/bin/python3",
            "/ros2_ws/src/webUI/gps_diagnostics.py"
            ],
        cwd="/ros2_ws",
        output="screen",
    )
    camera_status = ExecuteProcess(
        cmd=[
            "/ros2_ws/.venv/bin/python3",
            "/ros2_ws/src/webUI/camera_diagnostics.py"
            ],
        cwd="/ros2_ws",
        output="screen",
    )

    nodes = [
        #Node(
        #    namespace="Basler_left",
        #    package="pylon_ros2_camera_wrapper",
        #    executable="pylon_ros2_camera_wrapper",
        #    name="pylon_ros2_camera_node",
        #    output="screen",
        #    emulate_tty=True,
        #    parameters=[
        #        "/ros2_ws/config/basler_left.yaml",
        #        {
        #            "startup_user_set": "CurrentSetting",
        #            "enable_status_publisher": False,
        #            "enable_current_params_publisher": False,
        #        },
        #    ],
        #),
        #Node(
        #    namespace="Basler_middle",
        #    package="pylon_ros2_camera_wrapper",
        #    executable="pylon_ros2_camera_wrapper",
        #    name="pylon_ros2_camera_node",
        #    output="screen",
        #    emulate_tty=True,
        #    parameters=[
        #        "/ros2_ws/config/basler_middle.yaml",
        #        {
        #            "startup_user_set": "CurrentSetting",
        #            "enable_status_publisher": False,
        #            "enable_current_params_publisher": False,
        #        },
        #    ],
        #),
        #Node(
        #    namespace="Basler_right",
        #    package="pylon_ros2_camera_wrapper",
        #    executable="pylon_ros2_camera_wrapper",
        #    name="pylon_ros2_camera_node",
        #    output="screen",
        #    emulate_tty=True,
        #    parameters=[
        #        "/ros2_ws/config/basler_right.yaml",
        #        {
        #            "startup_user_set": "CurrentSetting",
        #            "enable_status_publisher": True,
        #            "enable_current_params_publisher": False,
        #        },
        #    ],
        #),
        Node(
            package="diagnostic_aggregator",
            executable="aggregator_node",
            name="analyzers",
            output="screen",
            parameters=[
                os.path.join(ws_dir, "src", "webUI", "diagnostic_aggregator.yaml")
            ],
        ),
        web_ui,
        lidar_status,
        gps_status,
        camera_status,
        #hemi_data_collection,
        #dome_data_collection,
        #left_data_collection,
        #middle_data_collection,
        #right_data_collection,
    ]
    return LaunchDescription(nodes)
