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

EXPECTED_HZ = {
    "lidar": 10.0,
    "camera": 10.0,
    "imu": 1000.0,
    "gnss": 10.0,
}

SENSOR_DISPLAY_NAMES = {
    "Basler_left": "Camera Left",
    "Basler_middle": "Camera Middle",
    "Basler_right": "Camera Right",
    "Lidar 1": "Lidar XT",
    "Lidar 2": "Lidar JT",
    "XSens IMU": "XSens IMU",
}

RED = 1 << 0  # D0
GREEN = 1 << 1  # D1
BLUE = 1 << 2  # D2
YELLOW = RED | GREEN


def classify_sensor_type(name: str) -> str | None:
    n = name.lower()

    if "lidar" in n:
        return "lidar"
    if "camera" in n:
        return "camera"
    if "imu" in n:
        return "imu"
    if "gnss" in n or "gps" in n:
        return "gnss"

    return None


def get_sensor_display_name(full_name: str, sensor_type=None) -> str:
    # Keep only the final diagnostic path component.
    name = full_name.rsplit("/", 1)[-1].strip()

    if sensor_type == "camera":
        while name.startswith("Camera "):
            name = name.removeprefix("Camera ").strip()

    elif sensor_type == "lidar":
        # Collapse repeated prefixes but retain one "Lidar ".
        while name.startswith("Lidar Lidar "):
            name = name.removeprefix("Lidar ").strip()

        if name in {"1", "2"}:
            name = f"Lidar {name}"

    return SENSOR_DISPLAY_NAMES.get(name, name)


def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def level_from_hz(hz, expected_hz):
    if hz is None or expected_hz is None:
        return None

    ratio = hz / expected_hz

    if ratio <= 0.70:
        return 2  # ERROR
    if ratio < 0.90:
        return 1  # WARN

    return 0  # OK


def worst_level(*levels):
    valid = [level for level in levels if level is not None]
    return max(valid) if valid else 3


def update_overall_status():
    sensor_levels = [sensor["level"] for sensor in diagnostic_data["sensors"]]
    gps_level = diagnostic_data["gps"]["level"]
    overall_level = worst_level(*sensor_levels, gps_level)
    diagnostic_data["overall_level"] = overall_level
    diagnostic_data["overall_status"] = diagnostic_level_to_text(overall_level)


def diagnostic_level_to_text(level) -> str:
    level = normalize_level(level)

    if level == 0:
        return "OK"
    if level == 1:
        return "WARN"
    if level == 2:
        return "ERROR"
    if level == 3:
        return "STALE"
    return "UNKNOWN"


diagnostic_data = {
    "diagnostics": {},
    "raw": [],
    "sensors": [],
    "overall_level": 3,
    "overall_status": "STALE",
    "last_update": None,
    "start_time": None,
    "collection_enabled": "false",
    "recording_message": "Data collection has not been started yet.",
    "gps": {
        "level": 3,
        "level_text": "WAITING",
        "emoji": "⚫",
        "message": "Waiting for satellite lock",
        "last_update": None,
        "satellites_used": None,
        "satellites_visible": None,
        "fix_status": None,
        "latitude": None,
        "longitude": None,
        "altitude": None,
        "speed": None,
        "hdop": None,
        "pdop": None,
        "interference": None,
        "spoofing": None,
        "rf_bands": None,
    },
}


def normalize_level(level):
    if isinstance(level, int):
        return level

    if isinstance(level, bytes):
        return level[0] if level else 3

    if isinstance(level, str):
        return ord(level[0]) if level else 3

    return 3


# URL format: ftdi://vendor:product/interface
# 0x0403:0x6014 is FT232H; interface 1 is ADBUS (GPIO AD0..AD7)
gpio = GpioAsyncController()
gpio.configure("ftdi://0x0403:0x6014/1", direction=0x07)  # D0..D2 as output
gpio.write(0x000)


class WebUINode(Node):
    def __init__(self):
        super().__init__("web_ui_node")

        self.data_collection_client = self.create_client(
            SetBool,
            "/set_data_collection_enabled",
        )

        # Subscribe to the standard diagnostic_aggregator output.
        # Sensor nodes should publish raw diagnostic_msgs/DiagnosticArray on /diagnostics.
        # diagnostic_aggregator groups them and republishes the aggregate tree here.
        self.create_subscription(
            DiagnosticArray,
            "/diagnostics_agg",
            self.diagnostics_callback,
            10,
        )

    def diagnostics_callback(self, msg: DiagnosticArray):
        global diagnostic_data

        diagnostic_data["last_update"] = time.time()

        diagnostics = {}
        raw = []
        sensors = []

        for status in msg.status:
            values = {kv.key: kv.value for kv in status.values}

            sensor_type = classify_sensor_type(status.name)
            hz = parse_float(values.get("hz"))
            expected_hz = EXPECTED_HZ.get(sensor_type) if sensor_type else None
            hz_level = level_from_hz(hz, expected_hz)
            diag_level = normalize_level(status.level)
            final_level = worst_level(diag_level, hz_level)
            final_level_text = diagnostic_level_to_text(final_level)

            diagnostic_item = {
                "name": status.name,
                "level": final_level,
                "level_text": final_level_text,
                "diag_level": diag_level,
                "diag_level_text": diagnostic_level_to_text(diag_level),
                "hz_level": hz_level,
                "hz_level_text": diagnostic_level_to_text(hz_level)
                if hz_level is not None
                else None,
                "message": status.message,
                "hardware_id": status.hardware_id,
                "values": values,
            }

            # Populate the dedicated GPS panel from the aggregated diagnostic.
            # Matching by its GNSS values avoids selecting the aggregator's group summary.
            if "satellites_used" in values or "gpsfix_available" in values:
                gps = diagnostic_data["gps"]
                gps.update(
                    {
                        "level": final_level,
                        "level_text": final_level_text,
                        "emoji": {0: "🟢", 1: "🟡", 2: "🔴", 3: "⚫"}.get(
                            final_level, "❓"
                        ),
                        "message": status.message,
                        "last_update": diagnostic_data["last_update"],
                        "satellites_used": parse_float(values.get("satellites_used")),
                        "satellites_visible": parse_float(values.get("satellites_visible")),
                        "fix_status": parse_float(values.get("fix_status")),
                        "latitude": parse_float(values.get("latitude")),
                        "longitude": parse_float(values.get("longitude")),
                        "altitude": parse_float(values.get("altitude")),
                        "speed": parse_float(values.get("speed")),
                        "hdop": parse_float(values.get("hdop")),
                        "pdop": parse_float(values.get("pdop")),
                        "interference": parse_float(values.get("interference")),
                        "spoofing": parse_float(values.get("spoofing")),
                        "rf_bands": parse_float(values.get("rf_bands")),
                    }
                )

            diagnostics[status.name] = diagnostic_item
            raw.append(diagnostic_item)

            # Aggregator group entries do not contain an Hz value and should
            # not be displayed as individual sensors.
            if sensor_type is None or hz is None:
                continue

            packet_loss = values.get("packet_loss") or values.get("packet_loss_count")
            sensor_name = get_sensor_display_name(
                status.name,
                sensor_type,
            )

            sensors.append(
                {
                    "name": sensor_name,
                    "full_name": status.name,
                    "sensor_type": sensor_type,
                    "level": final_level,
                    "level_text": final_level_text,
                    "diag_level": diag_level,
                    "diag_level_text": diagnostic_level_to_text(diag_level),
                    "hz_level": hz_level,
                    "hz_level_text": diagnostic_level_to_text(hz_level)
                    if hz_level is not None
                    else None,
                    "emoji": {
                        0: "🟢",
                        1: "🟡",
                        2: "🔴",
                        3: "⚫",
                    }.get(final_level, "❓"),
                    "message": status.message,
                    "hz": hz,
                    "expected_hz": expected_hz,
                    "packet_loss": packet_loss,
                    "values": values,
                }
            )

        diagnostic_data["diagnostics"] = diagnostics
        diagnostic_data["raw"] = raw
        diagnostic_data["sensors"] = sorted(sensors, key=lambda item: item["full_name"])
        update_overall_status()

        overall_level = diagnostic_data["overall_level"]
        if overall_level == 3:
            gpio.write(BLUE)
        elif overall_level == 2:
            gpio.write(RED)
        elif overall_level == 1:
            gpio.write(YELLOW)
        else:
            gpio.write(GREEN)

    def set_data_collection(self, enabled: bool):
        if not self.data_collection_client.wait_for_service(timeout_sec=0.5):
            return {
                "success": False,
                "message": "Data collection service is not available",
            }

        request = SetBool.Request()
        request.data = enabled

        future = self.data_collection_client.call_async(request)

        timeout_time = time.time() + 2.0
        while rclpy.ok() and not future.done():
            if time.time() > timeout_time:
                return {
                    "success": False,
                    "message": "Data collection service timed out",
                }
            time.sleep(0.01)

        result = future.result()

        if result is None:
            return {
                "success": False,
                "message": "Data collection service did not respond",
            }

        return {
            "success": result.success,
            "message": result.message,
        }


rclpy.init()
ros_node = WebUINode()

ros_thread = threading.Thread(
    target=rclpy.spin,
    args=(ros_node,),
    daemon=True,
)
ros_thread.start()


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
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
