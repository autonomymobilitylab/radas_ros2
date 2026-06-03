import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import PointCloud2
import rosbag2_py
import os
import shutil

class cloud_reader(Node):
    def __init__(self):
        super().__init__('cloud_reader')
        import os
        self.get_logger().info(f'CWD: {os.getcwd()}')
        self.reader = rosbag2_py.SequentialReader()
        storage_options = rosbag2_py.StorageOptions(
            uri='clouds',
            storage_id='mcap')
        converter_options = rosbag2_py.ConverterOptions(
            input_serialization_format='cdr',
            output_serialization_format='cdr'
        )
        self.reader.open(storage_options, converter_options)

        self.pub_xt = self.create_publisher(PointCloud2, '/lidar_points_xt', 10)
        self.pub_jt = self.create_publisher(PointCloud2, '/lidar_points_jt', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)

    def timer_callback(self):
        while self.reader.has_next():
            topic, data, timestamp = self.reader.read_next()
            msg = deserialize_message(data, PointCloud2)
            if topic == '/lidar_points_xt':
                self.pub_xt.publish(msg)
            elif topic == '/lidar_points_jt':
                self.pub_jt.publish(msg)
            self.get_logger().info(f'Published to {topic}')
            break


def main():
    rclpy.init()
    node = cloud_reader()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
