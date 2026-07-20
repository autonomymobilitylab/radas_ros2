import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.node import Node
from sensor_msgs.msg import Image


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


class CameraDiagnostics(Node):
    """Publish one normalized diagnostic status for each Basler camera."""

    EXPECTED_HZ = 10.0
    RATE_WINDOW_SECONDS = 2.0
    IMAGE_TIMEOUT_SECONDS = 2.0
    DIAGNOSTIC_TIMEOUT_SECONDS = 5.0

    CAMERAS = {
        "Basler_left": "/Basler_left/pylon_ros2_camera_node/image_raw",
        "Basler_middle": "/Basler_middle/pylon_ros2_camera_node/image_raw",
        "Basler_right": "/Basler_right/pylon_ros2_camera_node/image_raw",
    }

    def __init__(self):
        super().__init__("camera_diagnostics")

        self.camera_data = {
            hardware_id: {
                "last_diagnostic_time": None,
                "last_image_time": None,
                "image_times": [],
                "availability_level": None,
                "availability_message": "Waiting for camera diagnostics",
                "calibration_message": "Unknown",
            }
            for hardware_id in self.CAMERAS
        }

        self.create_subscription(
            DiagnosticArray,
            "/diagnostics",
            self.diagnostics_callback,
            10,
        )

        for hardware_id, topic in self.CAMERAS.items():
            self.create_subscription(
                Image,
                topic,
                lambda msg, camera=hardware_id: self.image_callback(camera),
                10,
            )

            self.get_logger().info(f"Calculating {hardware_id} frequency from {topic}")

        self.publisher = self.create_publisher(
            DiagnosticArray,
            "/diagnostics",
            10,
        )

        self.create_timer(1.0, self.publish_diagnostics)

    def image_callback(self, hardware_id):
        now = time.monotonic()
        camera = self.camera_data[hardware_id]

        camera["last_image_time"] = now
        camera["image_times"].append(now)
        camera["image_times"] = [
            timestamp
            for timestamp in camera["image_times"]
            if now - timestamp <= self.RATE_WINDOW_SECONDS
        ]

    def diagnostics_callback(self, msg: DiagnosticArray):
        now = time.monotonic()

        for status in msg.status:
            # Ignore diagnostics published by this node itself.
            if status.name.startswith("Camera/"):
                continue

            name = status.name.lower()

            if "pylon_ros2_camera_node" not in name:
                continue

            hardware_id = status.hardware_id.strip()

            if hardware_id not in self.camera_data:
                continue

            camera = self.camera_data[hardware_id]
            camera["last_diagnostic_time"] = now

            if "camera_availability" in name:
                camera["availability_level"] = normalize_level(status.level)
                camera["availability_message"] = status.message

            elif "intrinsic_calibration" in name:
                # Calibration is displayed as a detail but does not make a
                # connected and streaming camera fail.
                camera["calibration_message"] = status.message

    def calculate_hz(self, camera, now):
        camera["image_times"] = [
            timestamp
            for timestamp in camera["image_times"]
            if now - timestamp <= self.RATE_WINDOW_SECONDS
        ]

        return len(camera["image_times"]) / self.RATE_WINDOW_SECONDS

    def rate_level(self, camera, hz, now):
        last_image_time = camera["last_image_time"]

        if (
            last_image_time is None
            or now - last_image_time > self.IMAGE_TIMEOUT_SECONDS
        ):
            return DiagnosticStatus.STALE, "No image data"

        ratio = hz / self.EXPECTED_HZ

        if ratio <= 0.70:
            return DiagnosticStatus.ERROR, "Low frame rate"

        if ratio < 0.90:
            return DiagnosticStatus.WARN, "Low frame rate"

        return DiagnosticStatus.OK, "Streaming"

    def publish_diagnostics(self):
        now = time.monotonic()

        array = DiagnosticArray()
        array.header.stamp = self.get_clock().now().to_msg()

        for hardware_id in self.CAMERAS:
            camera = self.camera_data[hardware_id]

            hz = self.calculate_hz(camera, now)
            hz_level, hz_message = self.rate_level(camera, hz, now)

            last_diagnostic_time = camera["last_diagnostic_time"]
            availability_level = camera["availability_level"]

            if (
                last_diagnostic_time is None
                or now - last_diagnostic_time > self.DIAGNOSTIC_TIMEOUT_SECONDS
            ):
                final_level = DiagnosticStatus.STALE
                message = "Waiting for camera diagnostics"

            elif availability_level is None:
                final_level = DiagnosticStatus.STALE
                message = "Waiting for camera availability"

            elif availability_level != DiagnosticStatus.OK:
                final_level = availability_level
                message = camera["availability_message"]

            else:
                final_level = hz_level
                message = hz_message

            status = DiagnosticStatus()
            status.name = f"Camera/{hardware_id}"
            status.hardware_id = hardware_id
            status.level = ros_level(final_level)
            status.message = message
            status.values = [
                KeyValue(
                    key="hz",
                    value=f"{hz:.1f}",
                ),
                KeyValue(
                    key="availability",
                    value=camera["availability_message"],
                ),
                KeyValue(
                    key="calibration",
                    value=camera["calibration_message"],
                ),
            ]

            array.status.append(status)

        self.publisher.publish(array)


def main():
    rclpy.init()
    node = CameraDiagnostics()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
