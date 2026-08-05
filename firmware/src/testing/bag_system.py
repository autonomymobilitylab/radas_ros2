import rclpy
from rclpy.node import Node
from rclpy.serialization import serialize_message

from sensor_msgs.msg import PointCloud2, Image, CameraInfo, MagneticField
from geometry_msgs.msg import Vector3Stamped
from gps_msgs.msg import GPSFix
from tf2_msgs.msg import TFMessage

import gc
from datetime import datetime
from pathlib import Path
from threading import Lock

import rosbag2_py
from rosbag2_interfaces.srv import Pause, Resume, Record, Stop

class SystemRecorder(Node):
    def __init__(self):
        super().__init__('system_recorder')

        self.writer = None
        self.recording = False
        self.paused = False
        self.writer_lock = Lock()

        self.bag_root = Path('/data/rosbags')
        self.bag_root.mkdir(parents=True, exist_ok=True)

        # The list of all recorded topics
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
        self.create_control_services()
        self.create_bag_subscriptions()

        self.get_logger().info('System recorder node started.')
        self.get_logger().info('Recorder is idle. Call /system_recorder/record to start recording.')

    # Creation of services which are used to control the bag recordings
    def create_control_services(self):
        self.record_service = self.create_service(
            Record,
            '~/record',
            self.record_callback
        )
        self.stop_service = self.create_service(
            Stop,
            '~/stop',
            self.stop_callback
        )
        self.pause_service = self.create_service(
            Pause,
            '~/pause',
            self.pause_callback
        )
        self.resume_service = self.create_service(
            Resume,
            '~/resume',
            self.resume_callback
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

    def record_callback(self, request, response):
        with self.writer_lock:
            if self.recording:
                self.get_logger().warn('Record request rejected: recorder is already recording.')

                self.set_service_response(
                    response, 
                    success=False,
                    message='Recorder is already recording.'
                )
                return response

            requested_uri = getattr(request, 'uri', '')

            if requested_uri:
                bag_path = Path(requested_uri)

                # If the user gives only a bag name, place it under /data.
                if not bag_path.is_absolute():
                    bag_path = self.bag_root / bag_path
            else:
                # If no URI is given, create a unique recognizable name.
                bag_name = datetime.now().strftime('system_recording_%Y-%m-%d_%H-%M-%S')
                bag_path = self.bag_root / bag_name

            try:
                self.open_bag(bag_path)

                self.recording = True
                self.paused = False

                self.get_logger().info(f'Recording started: {bag_path}')

                self.set_service_response(
                    response,
                    success=True,
                    message=f'Recording started: {bag_path}'
                )

            except Exception as exc:
                self.writer = None
                self.recording = False
                self.paused = False

                self.get_logger().error(f'Failed to start recording: {exc}')

                self.set_service_response(
                    response,
                    success=False,
                    message=f'Failed to start recording: {exc}'
                )

            return response

    def stop_callback(self, request, response):
        with self.writer_lock:
            if not self.recording:
                self.get_logger().warn('Stop request rejected: recorder is not recording.')

                self.set_service_response(
                    response,
                    success=False,
                    message='Recorder is not recording.'
                )
                return response

            try:
                self.close_bag()

                self.recording = False
                self.paused = False

                self.get_logger().info('Recording stopped.')

                self.set_service_response(
                    response,
                    success=True,
                    message='Recording stopped.'
                )

            except Exception as exc:
                self.get_logger().error(f'Failed to stop recording: {exc}')

                self.set_service_response(
                    response,
                    success=False,
                    message=f'Failed to stop recording: {exc}'
                )

            return response

    def pause_callback(self, request, response):
        with self.writer_lock:
            if not self.recording:
                self.get_logger().warn('Pause request ignored: recorder is not recording.')
                return response

            if self.paused:
                self.get_logger().warn('Pause request ignored: recorder is already paused.')
                return response

            self.paused = True
            self.get_logger().info('Recording paused.')

            return response

    def resume_callback(self, request, response):
        with self.writer_lock:
            if not self.recording:
                self.get_logger().warn('Resume request ignored: recorder is not recording.')
                return response

            if not self.paused:
                self.get_logger().warn('Resume request ignored: recorder is not paused.')
                return response

            self.paused = False
            self.get_logger().info('Recording resumed.')

            return response
        
    def open_bag(self, bag_path: Path):
        bag_path.parent.mkdir(parents=True, exist_ok=True)
        self.writer = rosbag2_py.SequentialWriter()

        storage_options = rosbag2_py.StorageOptions(
            uri=str(bag_path),
            storage_id='mcap'
        )

        converter_options = rosbag2_py.ConverterOptions('', '')
        self.writer.open(storage_options, converter_options)
        self.create_bag_topics()

    def close_bag(self):
        if self.writer is None:
            return

        if hasattr(self.writer, 'close'):
            self.writer.close()

        self.writer = None
        gc.collect()

    def create_bag_topics(self):
        if self.writer is None:
            raise RuntimeError('Cannot create bag topics because writer is not open.')

        for msg_type, topic_names in self.topics.items():
            type_name = self.get_ros_type_name(msg_type)

            for topic_name in topic_names:
                topic_info = rosbag2_py.TopicMetadata(
                    id=0,
                    name=topic_name,
                    type=type_name,
                    serialization_format='cdr'
                )

                self.writer.create_topic(topic_info)

    def write_msg(self, topic_name, msg):
        with self.writer_lock:
            if not self.recording:
                return

            if self.paused:
                return

            if self.writer is None:
                return

            timestamp = self.get_clock().now().nanoseconds

            self.writer.write(
                topic_name,
                serialize_message(msg),
                timestamp
            )

    @staticmethod
    def get_ros_type_name(msg_type):
        return f'{msg_type.__module__.replace(".", "/")}/{msg_type.__name__}'

    @staticmethod
    def set_service_response(response, success=None, message=None):
        """
        Different ROS 2 versions may expose slightly different service response fields.
        This helper sets fields only if they exist.
        """
        if success is not None and hasattr(response, 'success'):
            response.success = success

        if message is not None and hasattr(response, 'message'):
            response.message = message


def main():
    rclpy.init()

    node = SystemRecorder()

    try:
        rclpy.spin(node)
    finally:
        if node.recording:
            node.get_logger().info('Node shutting down while recording. Closing bag.')
            node.close_bag()

        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()