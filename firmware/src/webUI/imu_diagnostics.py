import time
from collections import deque

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.node import Node
from sensor_msgs.msg import Imu
from rclpy.qos import qos_profile_sensor_data

def normalize_level(level):
    """Convert a ROS diagnostic level to a Python integer."""
    if isinstance(level, int):
        return level

    if isinstance(level, (bytes, bytearray)):
        return level[0] if level else DiagnosticStatus.STALE

    if isinstance(level, str):
        return ord(level[0]) if level else DiagnosticStatus.STALE

    try:
        return int(level)
    except (TypeError, ValueError):
        return DiagnosticStatus.STALE


def ros_level(level):
    """Encode a diagnostic level for the Jazzy generated Python message."""
    value = normalize_level(level)
    return bytes([max(0, min(3, value))])

class ImuDiagnostics(Node):
    """Publish normalized XSens IMU diagnostics on /diagnostics."""

    TOPIC = "/imu/data"
    EXPECTED_HZ = 100.0
    RATE_WINDOW_SECONDS = 2.0
    MESSAGE_TIMEOUT_SECONDS = 2.0

    def __init__(self):
        super().__init__("imu_diagnostics")

        self.last_message_time = None
        self.message_times = deque()

        self.create_subscription(Imu, self.TOPIC, self.imu_callback, qos_profile_sensor_data)
        self.publisher = self.create_publisher(DiagnosticArray, "/diagnostics", 10)
        self.create_timer(1.0, self.publish_diagnostics)

        self.get_logger().info(f"Calculating XSens IMU frequency from {self.TOPIC}")

    def imu_callback(self, _msg: Imu):
        now = time.monotonic()
        self.last_message_time = now
        self.message_times.append(now)
        self.prune_samples(now)

    def prune_samples(self, now):
        cutoff = now - self.RATE_WINDOW_SECONDS
        while self.message_times and self.message_times[0] < cutoff:
            self.message_times.popleft()

    def calculate_hz(self, now):
        self.prune_samples(now)

        if len(self.message_times) < 2:
            return 0.0

        elapsed = self.message_times[-1] - self.message_times[0]
        if elapsed <= 0.0:
            return 0.0

        return (len(self.message_times) - 1) / elapsed

    def publish_diagnostics(self):
        now = time.monotonic()
        hz = self.calculate_hz(now)

        if (
            self.last_message_time is None
            or now - self.last_message_time > self.MESSAGE_TIMEOUT_SECONDS
        ):
            level = DiagnosticStatus.STALE
            message = f"No data on {self.TOPIC}"
        else:
            ratio = hz / self.EXPECTED_HZ

            if ratio <= 0.70:
                level = DiagnosticStatus.ERROR
                message = "Low data rate"
            elif ratio < 0.90:
                level = DiagnosticStatus.WARN
                message = "Low data rate"
            else:
                level = DiagnosticStatus.OK
                message = "Streaming"

        status = DiagnosticStatus()
        status.name = "IMU/XSens IMU"
        status.hardware_id = "xsens_mti"
        status.level = ros_level(level)
        status.message = message
        status.values = [
            KeyValue(key="hz", value=f"{hz:.1f}"),
            KeyValue(key="topic", value=self.TOPIC),
        ]

        array = DiagnosticArray()
        array.header.stamp = self.get_clock().now().to_msg()
        array.status.append(status)
        self.publisher.publish(array)


def main():
    rclpy.init()
    node = ImuDiagnostics()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
