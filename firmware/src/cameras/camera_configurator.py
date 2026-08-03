import sys
from typing import Iterable

import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool
from pylon_ros2_camera_interfaces.srv import SetIntegerValue


CAMERAS = ("Basler_left", "Basler_middle", "Basler_right")
TRIGGER_SOURCE_LINE_1 = 1


class HardwareTriggerConfigurator(Node):
    def __init__(self) -> None:
        super().__init__("basler_hardware_trigger_configurator")

    def configure_camera(self, camera_name: str) -> bool:
        node_path = f"/{camera_name}/pylon_ros2_camera_node"
        source_service = f"{node_path}/set_trigger_source"
        mode_service = f"{node_path}/set_trigger_mode"

        source_client = self.create_client(SetIntegerValue, source_service)
        mode_client = self.create_client(SetBool, mode_service)

        self.get_logger().info(f"Waiting for {camera_name} trigger services...")
        source_client.wait_for_service()
        mode_client.wait_for_service()

        source_request = SetIntegerValue.Request()
        source_request.value = TRIGGER_SOURCE_LINE_1
        source_future = source_client.call_async(source_request)
        rclpy.spin_until_future_complete(self, source_future)

        if not self._call_succeeded(source_future, source_service):
            return False

        mode_request = SetBool.Request()
        mode_request.data = True
        mode_future = mode_client.call_async(mode_request)
        rclpy.spin_until_future_complete(self, mode_future)

        if not self._call_succeeded(mode_future, mode_service):
            return False

        self.get_logger().info(
            f"{camera_name} configured for hardware triggering on Line 1."
        )
        return True

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
