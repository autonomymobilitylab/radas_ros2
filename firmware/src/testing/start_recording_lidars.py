from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    yaml_config_xt='/ros2_ws/config/config_xt.yaml'
    yaml_config_jt='/ros2_ws/config/config_jt.yaml'
    return LaunchDescription([
        Node(
            namespace='hesai_ros_driver_xt',
            package='hesai_ros_driver',
            executable='hesai_ros_driver_node',
            output='screen',
            parameters=[{'config_path': yaml_config_xt}]
        ),
        Node(
            namespace='hesai_ros_driver_jt',
            package='hesai_ros_driver',
            executable='hesai_ros_driver_node',
            output='screen',
            parameters=[{'config_path': yaml_config_jt}]
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['--x', '0', '--y', '0', '--z', '0',
                       '--roll', '0', '--pitch', '0', '--yaw', '0',
                       '--frame-id', 'base_link',
                       '--child-frame-id', 'hesai_lidar_xt']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['--x', '0', '--y', '0', '--z', '0',
                       '--roll', '0', '--pitch', '0', '--yaw', '0',
                       '--frame-id', 'base_link',
                       '--child-frame-id', 'hesai_lidar_jt']
        ),

        ExecuteProcess(
            cmd=['python3', '/ros2_ws/src/bag_clouds.py'],
            name='cloud_recorder',
            output='screen'
        )
    ])