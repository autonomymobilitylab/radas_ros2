from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, TimerAction

from ament_index_python.packages import get_package_share_directory
import os
from dotenv import load_dotenv

load_dotenv("/ros2_ws/src/.env")

def generate_launch_description():
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
    imu_status = ExecuteProcess(
        cmd=[
            "/ros2_ws/.venv/bin/python3",
            "/ros2_ws/src/webUI/imu_diagnostics.py",
            ],
        cwd="/ros2_ws",
        output="screen",
    )
    ntrip_client = ExecuteProcess(
        cmd=[
            "/ros2_ws/src/.venv/bin/python3",
            "/ros2_ws/src/ntrip_client/ros_ntrip_client.py",
        ],
        additional_env={
            "NTRIPUSER": os.getenv("NTRIPUSER"),
            "NTRIPPASS": os.getenv("NTRIPPASS"),
        },
        output="screen",
        respawn=True,
        respawn_delay=5.0,
    )
    camera_configurator = ExecuteProcess(
        cmd=[
            "/ros2_ws/src/.venv/bin/python3",
            "/ros2_ws/src/cameras/camera_configurator.py",
        ],
        cwd="/ros2_ws",
        output="screen",
    )
    system_recorder = ExecuteProcess(
        cmd=['python3', '/ros2_ws/src/bag_manager/bag_manager.py'],
        output='screen'
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
                "/ros2_ws/config/cameras/basler_left.yaml",
                {
                    "startup_user_set": "UserSet1",
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
                "/ros2_ws/config/cameras/basler_middle.yaml",
                {
                    "startup_user_set": "UserSet1",
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
                "/ros2_ws/config/cameras/basler_right.yaml",
                {
                    "startup_user_set": "UserSet1",
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
                    "config_path": "/ros2_ws/config/lidars/xt32.yaml"
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
                    "config_path": "/ros2_ws/config/lidars/jt128.yaml"
                }
            ],
        ),
        Node(
            package="diagnostic_aggregator",
            executable="aggregator_node",
            name="analyzers",
            output="screen",
            parameters=[
                os.path.join(ws_dir, "src", "webUI", "diagnostic_aggregator.yaml")
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
        Node(
            package='xsens_mti_ros2_driver',
            executable='xsens_mti_node',
            name='xsens_mti_node',
            namespace="Imu",
            output='screen',
            parameters=["/ros2_ws/config/xsens_param.yaml"],
        ),
        web_ui,
        lidar_status,
        gps_status,
        camera_status,
        camera_configurator,
        ntrip_client,
        imu_status,
        system_recorder,
    ]
    return LaunchDescription(nodes)
