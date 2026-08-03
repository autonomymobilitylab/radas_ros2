import sys
import time
from typing import Iterable, Type

import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool, Trigger
from pylon_ros2_camera_interfaces.srv import (
    GetPtpStatus,
    SetIntegerValue,
    SetROI,
)


CAMERAS = ("Basler_left", "Basler_middle", "Basler_right")
TRIGGER_SOURCE_LINE_1 = 1
CHUNK_SELECTOR_TIMESTAMP = 7

PTP_PRIORITY = 127
PTP_PROFILE = 1
PTP_NETWORK_MODE = 2
PTP_SLAVE_TIMEOUT_SEC = 30.0
PTP_POLL_INTERVAL_SEC = 0.5

ROI_X_OFFSET = 0
ROI_Y_OFFSET = 0
ROI_WIDTH = 1920
ROI_HEIGHT = 1200
ROI_DO_RECTIFY = False

SERVICE_WAIT_TIMEOUT_SEC = 10.0


class HardwareTriggerConfigurator(Node):
    def __init__(self) -> None:
        super().__init__("basler_hardware_trigger_configurator")

        self.declare_parameter("use_sim_time", False)
        if bool(self.get_parameter("use_sim_time").value):
            raise RuntimeError("use_sim_time must remain false for this PTP setup")

    def configure_camera(self, camera_name: str) -> bool:
        node_path = f"/{camera_name}/pylon_ros2_camera_node"
        self.get_logger().info(f"Configuring {camera_name} at {node_path}")

        if not self._call_trigger(node_path, "stop_grabbing"):
            return False

        configuration_ok = all(
            (
                self._set_bool(node_path, "enable_ptp_management_protocol", True),
                self._set_integer(node_path, "set_ptp_priority", PTP_PRIORITY),
                self._set_integer(node_path, "set_ptp_profile", PTP_PROFILE),
                self._set_integer(node_path, "set_ptp_network_mode", PTP_NETWORK_MODE),
                self._set_bool(node_path, "enable_two_step_operation", False),
                self._set_bool(node_path, "enable_ptp", True),
                self._set_roi(node_path),
                self._set_bool(node_path, "set_chunk_mode_active", True),
                self._set_integer(
                    node_path, "set_chunk_selector", CHUNK_SELECTOR_TIMESTAMP
                ),
                self._set_bool(node_path, "set_chunk_enable", True),
                self._set_integer(
                    node_path, "set_trigger_source", TRIGGER_SOURCE_LINE_1
                ),
                self._set_bool(node_path, "set_trigger_mode", True),
            )
        )

        if not configuration_ok:
            self.get_logger().error(f"Configuration failed for {camera_name}")
            return False

        if not self._wait_for_ptp_slave(node_path, camera_name):
            return False

        if not self._call_trigger(node_path, "start_grabbing"):
            return False

        self.get_logger().info(
            f"{camera_name}: PTP Slave, timestamp chunks enabled, "
            "ROI=1920x1200, hardware trigger=Line1"
        )
        return True

    def _set_bool(self, node_path: str, service: str, value: bool) -> bool:
        request = SetBool.Request()
        request.data = value
        return self._call_service(
            SetBool, f"{node_path}/{service}", request
        )

    def _set_integer(self, node_path: str, service: str, value: int) -> bool:
        request = SetIntegerValue.Request()
        request.value = value
        return self._call_service(
            SetIntegerValue, f"{node_path}/{service}", request
        )

    def _set_roi(self, node_path: str) -> bool:
        request = SetROI.Request()
        request.target_roi.x_offset = ROI_X_OFFSET
        request.target_roi.y_offset = ROI_Y_OFFSET
        request.target_roi.width = ROI_WIDTH
        request.target_roi.height = ROI_HEIGHT
        request.target_roi.do_rectify = ROI_DO_RECTIFY
        return self._call_service(SetROI, f"{node_path}/set_roi", request)

    def _call_trigger(self, node_path: str, service: str) -> bool:
        return self._call_service(
            Trigger, f"{node_path}/{service}", Trigger.Request()
        )

    def _wait_for_ptp_slave(self, node_path: str, camera_name: str) -> bool:
        service_name = f"{node_path}/get_ptp_status"
        client = self.create_client(GetPtpStatus, service_name)

        if not client.wait_for_service(timeout_sec=SERVICE_WAIT_TIMEOUT_SEC):
            self.get_logger().error(f"Service unavailable: {service_name}")
            self.destroy_client(client)
            return False

        deadline = time.monotonic() + PTP_SLAVE_TIMEOUT_SEC
        last_status = "unknown"

        try:
            while rclpy.ok() and time.monotonic() < deadline:
                future = client.call_async(GetPtpStatus.Request())
                rclpy.spin_until_future_complete(
                    self, future, timeout_sec=SERVICE_WAIT_TIMEOUT_SEC
                )

                if not future.done() or future.exception() is not None:
                    self.get_logger().warning(
                        f"{camera_name}: failed to read PTP status; retrying"
                    )
                    time.sleep(PTP_POLL_INTERVAL_SEC)
                    continue

                response = future.result()
                if response is None:
                    time.sleep(PTP_POLL_INTERVAL_SEC)
                    continue

                if hasattr(response, "success") and not response.success:
                    message = getattr(response, "message", "")
                    self.get_logger().warning(
                        f"{camera_name}: PTP status rejected: {message}"
                    )
                    time.sleep(PTP_POLL_INTERVAL_SEC)
                    continue

                last_status = str(getattr(response, "ptp_status", "unknown"))
                servo_status = str(
                    getattr(response, "ptp_servo_status", "unknown")
                )
                offset_ns = getattr(response, "ptp_offset", None)

                self.get_logger().info(
                    f"{camera_name}: PTP status={last_status}, "
                    f"servo={servo_status}, offset={offset_ns} ns"
                )

                if last_status.strip().lower() == "slave":
                    return True

                time.sleep(PTP_POLL_INTERVAL_SEC)
        finally:
            self.destroy_client(client)

        self.get_logger().error(
            f"{camera_name}: PTP did not reach Slave state within "
            f"{PTP_SLAVE_TIMEOUT_SEC:.1f}s (last status: {last_status})"
        )
        return False

    def _call_service(self, srv_type: Type, service_name: str, request) -> bool:
        client = self.create_client(srv_type, service_name)
        try:
            self.get_logger().info(f"Calling {service_name}")
            if not client.wait_for_service(timeout_sec=SERVICE_WAIT_TIMEOUT_SEC):
                self.get_logger().error(f"Service unavailable: {service_name}")
                return False

            future = client.call_async(request)
            rclpy.spin_until_future_complete(
                self, future, timeout_sec=SERVICE_WAIT_TIMEOUT_SEC
            )

            if not future.done():
                self.get_logger().error(f"Service timed out: {service_name}")
                return False

            return self._call_succeeded(future, service_name)
        finally:
            self.destroy_client(client)

    def _call_succeeded(self, future, service_name: str) -> bool:
        exception = future.exception()
        if exception is not None:
            self.get_logger().error(f"Service call failed for {service_name}: {exception}")
            return False

        response = future.result()
        if response is None:
            self.get_logger().error(f"Service call returned no response: {service_name}")
            return False

        if hasattr(response, "success") and not response.success:
            message = getattr(response, "message", "")
            self.get_logger().error(
                f"Service rejected request for {service_name}: {message}"
            )
            return False

        return True


def main(camera_names: Iterable[str] = CAMERAS) -> int:
    rclpy.init()
    configurator = HardwareTriggerConfigurator()

    try:
        results = [
            configurator.configure_camera(camera_name)
            for camera_name in camera_names
        ]
        return 0 if all(results) else 1
    except KeyboardInterrupt:
        return 130
    finally:
        configurator.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    sys.exit(main())
