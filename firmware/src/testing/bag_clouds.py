import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.serialization import serialize_message
from sensor_msgs.msg import PointCloud2
from sensor_msgs.msg import Imu
import rosbag2_py
import os
import shutil


class cloud_recorder(Node):
    def __init__(self):
        super().__init__('cloud_recorder')
        self.writer = rosbag2_py.SequentialWriter()

        storage_options = rosbag2_py.StorageOptions(
            uri = 'clouds',
            storage_id = 'mcap'
        )

        if os.path.exists('clouds'):
            self.get_logger().info('Removing existing bag directory...')
            shutil.rmtree('clouds')

        converter_options = rosbag2_py.ConverterOptions(
            input_serialization_format='cdr',
            output_serialization_format='cdr'
        )
        self.writer.open(storage_options, converter_options)

        for topic_name in ['/lidar_points_xt', '/lidar_points_jt']:
            topic_info = rosbag2_py.TopicMetadata(
                id=0,
                name=topic_name,
                type='sensor_msgs/msg/PointCloud2',
                serialization_format='cdr'
            )
            self.writer.create_topic(topic_info)

        topic_info = rosbag2_py.TopicMetadata(
            id=0,
            name = '/lidar_imu_jt',
            type = 'sensor_msgs/msg/Imu',
            serialization_format='cdr'
        )
        self.writer.create_topic(topic_info)

        self.create_subscription(
            PointCloud2, '/lidar_points_xt',
            lambda msg: self._write_msg('/lidar_points_xt', msg),
            qos_profile_sensor_data
        )
        self.create_subscription(
            PointCloud2, '/lidar_points_jt',
            lambda msg: self._write_msg('/lidar_points_jt', msg),
            qos_profile_sensor_data
        )

        self.create_subscription(
            Imu, '/lidar_imu_jt',
            lambda msg: self._write_msg('/lidar_imu_jt', msg),
            qos_profile_sensor_data
        )

    def _write_msg(self, topic_name: str, msg: PointCloud2):
        self.writer.write(
            topic_name,
            serialize_message(msg),
            self.get_clock().now().nanoseconds
        )

def main():
    rclpy.init()
    node = cloud_recorder()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()