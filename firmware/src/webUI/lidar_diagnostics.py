import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from hesai_ros_driver.msg import LossPacket


class LidarDiagnostics(Node):
    def __init__(self):
        super().__init__("lidar_diagnostics")

        self.last_msg_time = {
            "Lidar/Lidar 1": None,
            "Lidar/Lidar 2": None,
        }

        self.msg_times = {
            "Lidar/Lidar 1": [],
            "Lidar/Lidar 2": [],
        }

        self.packet_loss = {
            "Lidar/Lidar 1": None,
            "Lidar/Lidar 2": None,
        }

        self.packet_loss_total = {
            "Lidar/Lidar 1": None,
            "Lidar/Lidar 2": None,
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

        self.create_subscription(
            LossPacket,
            "/lidar_packets_loss_xt",
            lambda msg: self.packet_loss_cb("Lidar/Lidar 1", msg),
            10,
        )

        self.create_subscription(
            LossPacket,
            "/lidar_packets_loss_jt",
            lambda msg: self.packet_loss_cb("Lidar/Lidar 2", msg),
            10,
        )

        self.pub = self.create_publisher(DiagnosticArray, "/diagnostics", 10)
        self.create_timer(1.0, self.publish_diagnostics)

    def point_cb(self, name):
        now = time.time()
        self.last_msg_time[name] = now
        self.msg_times[name].append(now)
        self.msg_times[name] = [t for t in self.msg_times[name] if now - t <= 2.0]

    def packet_loss_cb(self, name, msg):
        total = msg.total_packet_count
        lost = msg.total_packet_loss_count

        self.packet_loss_total[name] = lost

        if total <= 0:
            self.packet_loss[name] = 0.0
        else:
            self.packet_loss[name] = lost / total

    def publish_diagnostics(self):
        now = time.time()
        msg = DiagnosticArray()
        msg.header.stamp = self.get_clock().now().to_msg()

        for name in self.msg_times:
            last = self.last_msg_time[name]
            times = self.msg_times[name]
            hz = len(times) / 2.0

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

            packet_loss = self.packet_loss[name]
            packet_loss_total = self.packet_loss_total[name]

            if packet_loss is not None:
                if packet_loss > 0.20:
                    level = max(level, DiagnosticStatus.ERROR)
                    text = "High packet loss"
                elif packet_loss > 0.05:
                    level = max(level, DiagnosticStatus.WARN)
                    text = "Packet loss"

            status = DiagnosticStatus()
            status.name = name
            status.level = level
            status.message = text
            status.hardware_id = name
            values = [
                KeyValue(key="hz", value=f"{hz:.1f}"),
            ]

            if packet_loss is not None:
                values.append(
                    KeyValue(key="packet_loss", value=f"{packet_loss * 100:.2f}%")
                )

            if packet_loss_total is not None:
                values.append(
                    KeyValue(key="packet_loss_count", value=str(packet_loss_total))
                )

            status.values = values

            msg.status.append(status)

        self.pub.publish(msg)


def main():
    rclpy.init()
    node = LidarDiagnostics()
    rclpy.spin(node)


if __name__ == "__main__":
    main()
