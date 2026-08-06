import time
from collections import deque

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue


class LidarDiagnostics(Node):
    def __init__(self):
        super().__init__("lidar_diagnostics")

        self.last_msg_time = {
            "Lidar/Lidar 1": None,
            "Lidar/Lidar 2": None,
        }

        self.msg_times = {
            "Lidar/Lidar 1": deque(),
            "Lidar/Lidar 2": deque(),
        }

        self.create_subscription(
            PointCloud2,
            "/lidar_points_xt",
            lambda msg: self.point_cb("Lidar/Lidar 1"),
            10,
        )

        self.create_subscription(
            PointCloud2,
            "/lidar_points_jt",
            lambda msg: self.point_cb("Lidar/Lidar 2"),
            10,
        )

        self.pub = self.create_publisher(DiagnosticArray, "/diagnostics", 10)
        self.create_timer(1.0, self.publish_diagnostics)

    def point_cb(self, name):
        now = time.monotonic()

        self.last_msg_time[name] = now

        times = self.msg_times[name]
        times.append(now)

        cutoff = now - 2.0
        while times and times[0] < cutoff:
            times.popleft()

    def calculate_hz(self, name):
        times = self.msg_times[name]

        if len(times) < 2:
            return 0.0

        elapsed = times[-1] - times[0]
        if elapsed <= 0.0:
            return 0.0

        return (len(times) - 1) / elapsed

    def publish_diagnostics(self):
        now = time.monotonic()
        msg = DiagnosticArray()
        msg.header.stamp = self.get_clock().now().to_msg()

        for name in self.msg_times:
            last = self.last_msg_time[name]
            hz = self.calculate_hz(name) / 2

            if last is None or now - last > 2.0:
                level = DiagnosticStatus.STALE
                text = "Stale"
            elif hz < 7.0:
                level = DiagnosticStatus.ERROR
                text = "Low rate"
            elif hz < 9.0:
                level = DiagnosticStatus.WARN
                text = "Low rate"
            else:
                level = DiagnosticStatus.OK
                text = "OK"

            status = DiagnosticStatus()
            status.name = name
            status.level = level
            status.message = text
            status.hardware_id = name
            status.values = [
                KeyValue(key="hz", value=f"{hz:.1f}"),
            ]

            msg.status.append(status)

        self.pub.publish(msg)


def main():
    rclpy.init()
    node = LidarDiagnostics()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
