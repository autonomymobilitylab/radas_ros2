from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


from pathlib import Path
from pyftdi.gpio import GpioAsyncController
import threading
import time

import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool
from diagnostic_msgs.msg import DiagnosticArray

BASE_DIR = Path(__file__).parent
app = FastAPI()

templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


diagnostic_data = {
    "lidar_1_hz": None,
    "lidar_2_hz": None,
    "camera_1_hz": None,
    "camera_2_hz": None,
    "camera_3_hz": None,
    "imu_hz": None,
    "gnss_hz": None,
    "last_update": None,
    "recording_message": "Data collection has not been started yet.",
}

# URL format: ftdi://vendor:product/interface
# 0x0403:0x6014 is FT232H; interface 1 is ADBUS (GPIO AD0..AD7)
gpio = GpioAsyncController()
gpio.configure('ftdi://0x0403:0x6014/1', direction=0x01)  # AD0 output
gpio.write(0x00)

class WebUINode(Node):
    def __init__(self):
        super().__init__("web_ui_node")

        self.data_collection_client = self.create_client(
            SetBool,
            "/set_data_collection_enabled"
        )

        self.create_subscription(
            DiagnosticArray,
            "/diagnostics",
            self.diagnostics_callback,
            10
        )

    def diagnostics_callback(self, msg: DiagnosticArray):
        global diagnostic_data

        diagnostic_data["last_update"] = time.time()

        for status in msg.status:
            for kv in status.values:
                if kv.key in diagnostic_data:
                    diagnostic_data[kv.key] = kv.value

    def set_data_collection(self, enabled: bool):
        if not self.data_collection_client.wait_for_service(timeout_sec=0.5):
            return {
                "success": False,
                "message": "Data collection service is not available"
            }

        request = SetBool.Request()
        request.data = enabled

        future = self.data_collection_client.call_async(request)

        timeout_time = time.time() + 2.0
        while rclpy.ok() and not future.done():
            if time.time() > timeout_time:
                return {
                    "success": False,
                    "message": "Data collection service timed out"
                }
            time.sleep(0.01)

        result = future.result()

        if result is None:
            return {
                "success": False,
                "message": "Data collection service did not respond"
            }

        return {
            "success": result.success,
            "message": result.message
        }


rclpy.init()
ros_node = WebUINode()

ros_thread = threading.Thread(
    target=rclpy.spin,
    args=(ros_node,),
    daemon=True
)
ros_thread.start()


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.get("/diagnostics")
async def get_diagnostics():
    return diagnostic_data


@app.post("/datacollection/start")
async def start_data_collection():
    diagnostic_data["collection_enabled"] = "true"
    diagnostic_data["recording_message"] = "Data collection started."
    gpio.write(0x01)  # AD0 high
    return ros_node.set_data_collection(True)


@app.post("/datacollection/stop")
async def stop_data_collection():
    diagnostic_data["collection_enabled"] = "false"
    diagnostic_data["recording_message"] = "Data collection stopped."
    gpio.write(0x00)  # AD0 low
    return ros_node.set_data_collection(False)