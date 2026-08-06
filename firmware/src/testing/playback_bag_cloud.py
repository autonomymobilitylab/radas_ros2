from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    rviz_config='/ros2_ws/config/rviz/rviz2.rviz'
    return LaunchDescription([
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
        Node(namespace='rviz2', package='rviz2', executable='rviz2', arguments=['-d', rviz_config]),
        ExecuteProcess(
            cmd=['python3', '/ros2_ws/src/bag_reader.py'],
            name='cloud_reader',
            output='screen'
        )
    ])
