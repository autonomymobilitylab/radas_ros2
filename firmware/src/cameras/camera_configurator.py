import sys
import time
from typing import Iterable, Type

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
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
DRIVER_READY_TIMEOUT_SEC = 60.0
DRIVER_READY_RETRY_INTERVAL_SEC = 1.0
STOP_SETTLE_SEC = 1.0
PTP_DISABLE_SETTLE_SEC = 0.5
WRITE_RETRY_COUNT = 3


class HardwareTriggerConfigurator(Node):
    def __init__(self) -> None:
        super().__init__("basler_hardware_trigger_configurator")

        results = self.set_parameters([Parameter("use_sim_time", Parameter.Type.BOOL, False)])
        if not results or not results[0].successful:
            reason = results[0].reason if results else "no parameter result"
            raise RuntimeError(f"Failed to set use_sim_time=false: {reason}")

    def configure_camera(self, camera_name: str) -> bool:
        node_path = f"/{camera_name}/pylon_ros2_camera_node"
        self.get_logger().info(f"Configuring {camera_name} at {node_path}")

        if not self._stop_grabbing_when_ready(node_path, camera_name):
            return False

        time.sleep(STOP_SETTLE_SEC)
        if not self._call_trigger(node_path, "stop_grabbing"):
            return False

        if not self._set_bool(node_path, "enable_ptp", False):
            self.get_logger().error(
                f"{camera_name}: failed to disable PTP before configuration"
            )
            return False
        time.sleep(PTP_DISABLE_SETTLE_SEC)

        configuration_ok = all(
            (
                self._set_bool(node_path, "enable_ptp_management_protocol", True),
                self._set_integer(node_path, "set_ptp_priority", PTP_PRIORITY),
                self._set_integer(node_path, "set_ptp_profile", PTP_PROFILE),
                self._set_integer(node_path, "set_ptp_network_mode", PTP_NETWORK_MODE),
                self._set_bool(node_path, "enable_two_step_operation", False),
                self._set_bool(node_path, "enable_ptp", True),
                self._set_bool(node_path, "set_chunk_mode_active", True),
                self._set_integer(
                    node_path, "set_chunk_selector", CHUNK_SELECTOR_TIMESTAMP
                ),
                self._set_bool(node_path, "set_chunk_enable", True),
                self._set_integer(
                    node_path, "set_trigger_source", TRIGGER_SOURCE_LINE_1
                ),
                self._set_bool(node_path, "set_trigger_mode", True),
                self._set_roi(node_path),
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

    def _stop_grabbing_when_ready(self, node_path: str, camera_name: str) -> bool:
        """Retry stop_grabbing until camera discovery has completed."""
        service_name = f"{node_path}/stop_grabbing"
        client = self.create_client(Trigger, service_name)
        deadline = time.monotonic() + DRIVER_READY_TIMEOUT_SEC
        attempt = 0

        self.get_logger().info(
            f"{camera_name}: waiting for camera discovery before stopping acquisition"
        )

        try:
            while rclpy.ok() and time.monotonic() < deadline:
                attempt += 1
                remaining = max(0.0, deadline - time.monotonic())
                wait_time = min(DRIVER_READY_RETRY_INTERVAL_SEC, remaining)

                if not client.wait_for_service(timeout_sec=wait_time):
                    self.get_logger().info(
                        f"{camera_name}: stop_grabbing service not available yet "
                        f"(attempt {attempt})"
                    )
                    continue

                future = client.call_async(Trigger.Request())
                rclpy.spin_until_future_complete(
                    self, future, timeout_sec=SERVICE_WAIT_TIMEOUT_SEC
                )

                if future.done() and self._call_succeeded(
                    future, service_name, log_errors=False
                ):
                    self.get_logger().info(
                        f"{camera_name}: camera discovered; acquisition stopped"
                    )
                    return True

                reason = "driver has not initialized the camera yet"
                if future.done() and future.exception() is None:
                    response = future.result()
                    if response is not None:
                        reason = getattr(response, "message", reason) or reason

                self.get_logger().info(
                    f"{camera_name}: stop_grabbing not accepted yet "
                    f"(attempt {attempt}: {reason}); retrying"
                )
                time.sleep(DRIVER_READY_RETRY_INTERVAL_SEC)
        finally:
            self.destroy_client(client)

        self.get_logger().error(
            f"{camera_name}: stop_grabbing was not accepted within "
            f"{DRIVER_READY_TIMEOUT_SEC:.1f}s"
        )
        return False

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
        node_path = service_name.rsplit("/", 1)[0]

        for attempt in range(1, WRITE_RETRY_COUNT + 1):
            client = self.create_client(srv_type, service_name)
            try:
                self.get_logger().info(
                    f"Calling {service_name} (attempt {attempt}/{WRITE_RETRY_COUNT})"
                )
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

                if future.exception() is not None:
                    self.get_logger().error(
                        f"Service call failed for {service_name}: {future.exception()}"
                    )
                    return False

                response = future.result()
                if response is None:
                    self.get_logger().error(
                        f"Service call returned no response: {service_name}"
                    )
                    return False

                if not hasattr(response, "success") or response.success:
                    return True

                message = str(getattr(response, "message", ""))
                retryable = (
                    "node is not writable" in message.lower()
                    or "requires stopping image grabbing" in message.lower()
                )
                if not retryable or attempt == WRITE_RETRY_COUNT:
                    self.get_logger().error(
                        f"Service rejected request for {service_name}: {message}"
                    )
                    return False

                self.get_logger().warning(
                    f"{service_name} rejected while acquisition is active: {message}. "
                    "Stopping acquisition and retrying."
                )
            finally:
                self.destroy_client(client)

            # Do not recurse through _call_service for stop_grabbing.
            stop_name = f"{node_path}/stop_grabbing"
            stop_client = self.create_client(Trigger, stop_name)
            try:
                if not stop_client.wait_for_service(
                    timeout_sec=SERVICE_WAIT_TIMEOUT_SEC
                ):
                    self.get_logger().error(f"Service unavailable: {stop_name}")
                    return False
                stop_future = stop_client.call_async(Trigger.Request())
                rclpy.spin_until_future_complete(
                    self, stop_future, timeout_sec=SERVICE_WAIT_TIMEOUT_SEC
                )
                if not stop_future.done() or not self._call_succeeded(
                    stop_future, stop_name
                ):
                    return False
            finally:
                self.destroy_client(stop_client)

            time.sleep(0.2)

        return False

    def _call_succeeded(
        self, future, service_name: str, *, log_errors: bool = True
    ) -> bool:
        exception = future.exception()
        if exception is not None:
            if log_errors:
                self.get_logger().error(
                    f"Service call failed for {service_name}: {exception}"
                )
            return False

        response = future.result()
        if response is None:
            if log_errors:
                self.get_logger().error(
                    f"Service call returned no response: {service_name}"
                )
            return False

        if hasattr(response, "success") and not response.success:
            if log_errors:
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
