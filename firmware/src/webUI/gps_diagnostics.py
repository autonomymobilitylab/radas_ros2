import math
import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from gps_msgs.msg import GPSFix
from rclpy.node import Node
from septentrio_gnss_driver.msg import AIMPlusStatus, RFStatus


class GpsDiagnostics(Node):
    FIX_TIMEOUT_SECONDS = 5.0
    AUX_TIMEOUT_SECONDS = 5.0

    def __init__(self):
        super().__init__("gps_diagnostics")

        self.last_fix_time = None
        self.last_aim_time = None
        self.last_rf_time = None

        self.fix = None
        self.interference = None
        self.spoofing = None
        self.rf_bands = None

        # These subscriptions are valid even before the topics have publishers.
        # ROS 2 connects them automatically when the receiver starts publishing.
        self.create_subscription(GPSFix, "/gpsfix", self.gpsfix_callback, 10)
        self.create_subscription(
            AIMPlusStatus, "/aimplusstatus", self.aimplus_callback, 10
        )
        self.create_subscription(RFStatus, "/rfstatus", self.rfstatus_callback, 10)

        self.publisher = self.create_publisher(DiagnosticArray, "/diagnostics", 10)
        self.create_timer(1.0, self.publish_diagnostics)

    def gpsfix_callback(self, msg: GPSFix):
        self.fix = msg
        self.last_fix_time = time.monotonic()

    def aimplus_callback(self, msg: AIMPlusStatus):
        self.interference = int(msg.interference)
        self.spoofing = int(msg.spoofing)
        self.last_aim_time = time.monotonic()

    def rfstatus_callback(self, msg: RFStatus):
        self.rf_bands = int(msg.n)
        self.last_rf_time = time.monotonic()

    @staticmethod
    def number(value, digits=None):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "--"

        if not math.isfinite(number):
            return "--"
        if digits is None:
            return str(number)
        return f"{number:.{digits}f}"

    def publish_diagnostics(self):
        now = time.monotonic()
        level = DiagnosticStatus.STALE
        message = "Waiting for GNSS receiver topics"

        fix_fresh = (
            self.last_fix_time is not None
            and now - self.last_fix_time <= self.FIX_TIMEOUT_SECONDS
        )
        aim_fresh = (
            self.last_aim_time is not None
            and now - self.last_aim_time <= self.AUX_TIMEOUT_SECONDS
        )
        rf_fresh = (
            self.last_rf_time is not None
            and now - self.last_rf_time <= self.AUX_TIMEOUT_SECONDS
        )

        if self.last_fix_time is not None and not fix_fresh:
            level = DiagnosticStatus.STALE
            message = "GNSS fix data timed out"
        elif fix_fresh and self.fix is not None:
            satellites_used = int(self.fix.status.satellites_used)
            fix_status = int(self.fix.status.status)

            if satellites_used <= 0 or fix_status < 0:
                level = DiagnosticStatus.WARN
                message = "No usable GNSS fix"
            else:
                level = DiagnosticStatus.OK
                message = "GNSS fix available"

        if aim_fresh and (
            (self.interference is not None and self.interference > 0)
            or (self.spoofing is not None and self.spoofing > 0)
        ):
            level = DiagnosticStatus.ERROR
            message = "GNSS interference or spoofing detected"

        status = DiagnosticStatus()
        status.name = "GNSS/GNSS Receiver"
        status.hardware_id = "septentrio_gnss"
        status.level = level
        status.message = message

        values = [
            KeyValue(key="gpsfix_available", value=str(fix_fresh).lower()),
            KeyValue(key="aimplus_available", value=str(aim_fresh).lower()),
            KeyValue(key="rfstatus_available", value=str(rf_fresh).lower()),
        ]

        if self.fix is not None:
            values.extend(
                [
                    KeyValue(
                        key="satellites_used",
                        value=str(int(self.fix.status.satellites_used)),
                    ),
                    KeyValue(
                        key="satellites_visible",
                        value=str(int(self.fix.status.satellites_visible)),
                    ),
                    KeyValue(
                        key="fix_status", value=str(int(self.fix.status.status))
                    ),
                    KeyValue(key="latitude", value=self.number(self.fix.latitude, 9)),
                    KeyValue(key="longitude", value=self.number(self.fix.longitude, 9)),
                    KeyValue(key="altitude", value=self.number(self.fix.altitude, 3)),
                    KeyValue(key="speed", value=self.number(self.fix.speed, 3)),
                    KeyValue(key="hdop", value=self.number(self.fix.hdop, 3)),
                    KeyValue(key="pdop", value=self.number(self.fix.pdop, 3)),
                ]
            )

        if self.interference is not None:
            values.append(
                KeyValue(key="interference", value=str(self.interference))
            )
        if self.spoofing is not None:
            values.append(KeyValue(key="spoofing", value=str(self.spoofing)))
        if self.rf_bands is not None:
            values.append(KeyValue(key="rf_bands", value=str(self.rf_bands)))

        status.values = values

        array = DiagnosticArray()
        array.header.stamp = self.get_clock().now().to_msg()
        array.status.append(status)
        self.publisher.publish(array)


def main():
    rclpy.init()
    node = GpsDiagnostics()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
