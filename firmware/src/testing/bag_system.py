import rclpy
from rclpy.node import Node

from sensor_msgs.msg import PointCloud2, Image, CameraInfo, MagneticField
from geometry_msgs.msg import Vector3Stamped
from gps_msgs.msg import GPSFix
from tf2_msgs.msg import TFMessage
from datetime import datetime
from rclpy.serialization import serialize_message
from pathlib import Path

import rosbag2_py

class SystemRecorder(Node):
    def __init__(self):
        super().__init__('system_recorder')

        self.writer = rosbag2_py.SequentialWriter()

        bag_root = Path('/data/rosbags')
        bag_root.mkdir(parents=True, exist_ok=True)

        bag_name = datetime.now().strftime('system_recording_%Y-%m-%d_%H-%M-%S')
        bag_path = bag_root / bag_name

        self.writer.open(
            rosbag2_py.StorageOptions(uri=str(bag_path), storage_id='mcap'),
            rosbag2_py.ConverterOptions('', '')
        )

        self.get_logger().info(f'Recording rosbag to: {bag_path}')


        self.topics = {
            PointCloud2: [
                '/lidar_points_xt',
                '/lidar_points_jt',
            ],
            Image: [
                '/Basler_left/pylon_ros2_camera_node/image_raw',
                '/Basler_middle/pylon_ros2_camera_node/image_raw',
                '/Basler_right/pylon_ros2_camera_node/image_raw',
            ],
            CameraInfo: [
                '/Basler_left/pylon_ros2_camera_node/camera_info',
                '/Basler_middle/pylon_ros2_camera_node/camera_info',
                '/Basler_right/pylon_ros2_camera_node/camera_info',
            ],
            Vector3Stamped: [
                '/imu/acceleration_hr',
                '/imu/angular_velocity_hr',
            ],
            MagneticField: ['/imu/mag'],
            GPSFix: ['/Gnss/gpsfix'],
            TFMessage: ['/tf_static'],
        }

        self.bag_subscriptions = []

        self.create_bag_topics()
        self.create_bag_subscriptions()

    def create_bag_topics(self):
        for msg_type, topic_names in self.topics.items():
            type_name = self.get_ros_type_name(msg_type)

            for topic_name in topic_names:
                self.writer.create_topic(
                    rosbag2_py.TopicMetadata(
                        id=0,
                        name=topic_name,
                        type=type_name,
                        serialization_format='cdr'
                    )
                )

    def create_bag_subscriptions(self):
        for msg_type, topic_names in self.topics.items():
            for topic_name in topic_names:
                sub = self.create_subscription(
                    msg_type,
                    topic_name,
                    lambda msg, topic_name=topic_name: self.write_msg(topic_name, msg),
                    10
                )

                self.bag_subscriptions.append(sub)

    def write_msg(self, topic_name, msg):
        timestamp = self.get_clock().now().nanoseconds

        self.writer.write(
            topic_name,
            serialize_message(msg),
            timestamp
        )

    @staticmethod
    def get_ros_type_name(msg_type):
        return f'{msg_type.__module__.replace(".", "/")}/{msg_type.__name__}'
    
def main():
    rclpy.init()
    node = SystemRecorder()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()