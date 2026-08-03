#!/usr/bin/env python3

import random

import rclpy
from rclpy.node import Node

from diagnostic_msgs.msg import (
    DiagnosticArray,
    DiagnosticStatus,
    KeyValue,
)


class DiagnosticTestPublisher(Node):
    def __init__(self):
        super().__init__("diagnostic_test_publisher")

        self.pub = self.create_publisher(
            DiagnosticArray,
            "/diagnostics",
            10,
        )

        self.timer = self.create_timer(1.0, self.publish_diagnostics)

    def make_status(
        self,
        name: str,
        hz: float,
        level: int,
        message: str,
    ):
        status = DiagnosticStatus()

        status.name = name
        status.hardware_id = name
        status.level = level
        status.message = message

        status.values = [
            KeyValue(key="hz", value=f"{hz:.1f}"),
            KeyValue(
                key="temperature",
                value=f"{random.uniform(30, 90):.1f}",
            ),
            KeyValue(
                key="packets_dropped",
                value=str(random.randint(0, 5)),
            ),
        ]

        return status

    def publish_diagnostics(self):
        msg = DiagnosticArray()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.status = [
            self.make_status(
                "Lidar/Lidar 1",
                random.uniform(4.5, 11.5),
                DiagnosticStatus.OK,
                "Running",
            ),
            self.make_status(
                "Lidar/Lidar 2",
                random.uniform(4.5, 11.5),
                DiagnosticStatus.OK,
                "Running",
            ),
            self.make_status(
                "Camera/Camera 1",
                random.uniform(4.5, 11.5),
                DiagnosticStatus.OK,
                "Running",
            ),
            self.make_status(
                "Camera/Camera 2",
                random.uniform(4.5, 11.5),
                DiagnosticStatus.OK,
                "Running",
            ),
            self.make_status(
                "Camera/Camera 3",
                random.uniform(4.5, 11.5),
                DiagnosticStatus.OK,
                "Running",
            ),
            self.make_status(
                "IMU",
                random.uniform(400, 1150),
                DiagnosticStatus.OK,
                "Running",
            ),
            self.make_status(
                "GNSS",
                random.uniform(7.5, 11.5),
                DiagnosticStatus.WARN
                if random.random() < 0.2
                else DiagnosticStatus.OK,
                "Weak signal"
                if random.random() < 0.2
                else "Running",
            ),
        ]

        self.pub.publish(msg)


def main():
    rclpy.init()

    node = DiagnosticTestPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()