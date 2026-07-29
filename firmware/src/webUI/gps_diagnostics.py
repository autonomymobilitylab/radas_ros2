import math
import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from gps_msgs.msg import GPSFix
from rclpy.node import Node
from septentrio_gnss_driver.msg import AIMPlusStatus, PVTGeodetic, RFStatus


class GpsDiagnostics(Node):
    FIX_TIMEOUT_SECONDS = 5.0
    AUX_TIMEOUT_SECONDS = 5.0

    def __init__(self):
        super().__init__("gps_diagnostics")

        self.last_fix_time = None
        self.last_pvt_time = None
        self.last_aim_time = None
        self.last_rf_time = None

        self.fix = None
        self.pvt = None
        self.interference = None
        self.spoofing = None
        self.rf_bands = None

        # These subscriptions are valid even before the topics have publishers.
        # ROS 2 connects them automatically when the receiver starts publishing.
        self.create_subscription(GPSFix, "/Gnss/gpsfix", self.gpsfix_callback, 10)
        self.create_subscription(
            PVTGeodetic, "/Gnss/pvtgeodetic", self.pvtgeodetic_callback, 10
        )
        self.create_subscription(
            AIMPlusStatus, "/Gnss/aimplusstatus", self.aimplus_callback, 10
        )
        self.create_subscription(RFStatus, "/Gnss/rfstatus", self.rfstatus_callback, 10)

        self.publisher = self.create_publisher(DiagnosticArray, "/diagnostics", 10)
        self.create_timer(1.0, self.publish_diagnostics)

    def gpsfix_callback(self, msg: GPSFix):
        self.fix = msg
        self.last_fix_time = time.monotonic()

    def pvtgeodetic_callback(self, msg: PVTGeodetic):
        self.pvt = msg
        self.last_pvt_time = time.monotonic()

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


    @staticmethod
    def position_mode(mode):
        # Septentrio stores the solution type in the low four bits.
        # Preserve the raw value separately in diagnostics.
        solution = int(mode) & 0x0F
        modes = {
            0: (DiagnosticStatus.ERROR, "No position"),
            1: (DiagnosticStatus.WARN, "Standalone GNSS"),
            2: (DiagnosticStatus.OK, "Differential GNSS"),
            4: (DiagnosticStatus.OK, "RTK fixed"),
            # Mode 5 is commonly RTK float, but keep the label explicitly
            # marked as unverified until confirmed against this receiver setup.
            5: (DiagnosticStatus.WARN, "Mode 5 (possibly RTK float)"),
        }
        return solution, modes.get(
            solution,
            (DiagnosticStatus.WARN, f"Unknown position mode ({solution})"),
        )

    def publish_diagnostics(self):
        now = time.monotonic()
        level = DiagnosticStatus.STALE
        message = "Waiting for /pvtgeodetic"

        fix_fresh = (
            self.last_fix_time is not None
            and now - self.last_fix_time <= self.FIX_TIMEOUT_SECONDS
        )
        pvt_fresh = (
            self.last_pvt_time is not None
            and now - self.last_pvt_time <= self.FIX_TIMEOUT_SECONDS
        )
        aim_fresh = (
            self.last_aim_time is not None
            and now - self.last_aim_time <= self.AUX_TIMEOUT_SECONDS
        )
        rf_fresh = (
            self.last_rf_time is not None
            and now - self.last_rf_time <= self.AUX_TIMEOUT_SECONDS
        )

        mode_raw = None
        mode = None
        mode_text = None

        if self.last_pvt_time is not None and not pvt_fresh:
            level = DiagnosticStatus.STALE
            message = "PVT geodetic mode data timed out"
        elif pvt_fresh and self.pvt is not None:
            mode_raw = int(self.pvt.mode)
            mode, (level, mode_text) = self.position_mode(mode_raw)
            message = mode_text

            if not fix_fresh:
                level = DiagnosticStatus.STALE
                message = f"{mode_text}; GPSFix data unavailable"

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
            KeyValue(key="pvtgeodetic_available", value=str(pvt_fresh).lower()),
            KeyValue(key="gpsfix_available", value=str(fix_fresh).lower()),
            KeyValue(key="aimplus_available", value=str(aim_fresh).lower()),
            KeyValue(key="rfstatus_available", value=str(rf_fresh).lower()),
        ]

        if mode_raw is not None:
            values.extend(
                [
                    KeyValue(key="position_mode_raw", value=str(mode_raw)),
                    KeyValue(key="position_mode", value=str(mode)),
                    KeyValue(key="position_mode_text", value=mode_text),
                ]
            )

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
