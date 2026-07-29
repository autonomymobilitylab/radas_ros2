#!/usr/bin/env python3

import base64
import math
import os
import select
import socket
import threading
import time
from datetime import datetime, timezone

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
import serial


class RosNtripClient(Node):
    def __init__(self) -> None:
        super().__init__("ntrip_client")

        self.declare_parameter("host", "opencaster.nls.fi")
        self.declare_parameter("port", 2101)
        self.declare_parameter("mountpoint", "VRS-FKP")
        self.declare_parameter("navsatfix_topic", "/Gnss/navsatfix")
        self.declare_parameter("serial_port", "/dev/ttyACM0")
        self.declare_parameter("serial_baudrate", 115200)
        self.declare_parameter("gga_interval", 5.0)
        self.declare_parameter("reconnect_delay", 5.0)

        self.host = str(self.get_parameter("host").value)
        self.port = int(self.get_parameter("port").value)
        self.mountpoint = str(self.get_parameter("mountpoint").value)
        self.serial_port = str(self.get_parameter("serial_port").value)
        self.serial_baudrate = int(self.get_parameter("serial_baudrate").value)
        self.gga_interval = float(self.get_parameter("gga_interval").value)
        self.reconnect_delay = float(self.get_parameter("reconnect_delay").value)

        self.username = os.environ.get("NTRIPUSER")
        self.password = os.environ.get("NTRIPPASS")

        if not self.username or not self.password:
            raise RuntimeError("NTRIPUSER and NTRIPPASS must be set in the environment")

        self.position_lock = threading.Lock()
        self.latest_fix: NavSatFix | None = None
        self.running = True

        topic = str(self.get_parameter("navsatfix_topic").value)
        self.subscription = self.create_subscription(
            NavSatFix,
            topic,
            self.fix_callback,
            10,
        )

        self.worker = threading.Thread(
            target=self.connection_loop,
            daemon=True,
        )
        self.worker.start()

        self.get_logger().info(
            f"Waiting for position on {topic}; RTCM output: {self.serial_port}"
        )

    def fix_callback(self, message: NavSatFix) -> None:
        if (
            not math.isfinite(message.latitude)
            or not math.isfinite(message.longitude)
            or not math.isfinite(message.altitude)
        ):
            return

        # status < 0 means no position fix.
        if message.status.status < 0:
            return

        with self.position_lock:
            self.latest_fix = message

    @staticmethod
    def decimal_to_nmea(
        value: float,
        is_latitude: bool,
    ) -> tuple[str, str]:
        absolute = abs(value)
        degrees = int(absolute)
        minutes = (absolute - degrees) * 60.0

        if is_latitude:
            coordinate = f"{degrees:02d}{minutes:09.6f}"
            hemisphere = "N" if value >= 0 else "S"
        else:
            coordinate = f"{degrees:03d}{minutes:09.6f}"
            hemisphere = "E" if value >= 0 else "W"

        return coordinate, hemisphere

    @staticmethod
    def add_checksum(sentence_body: str) -> str:
        checksum = 0

        for character in sentence_body:
            checksum ^= ord(character)

        return f"${sentence_body}*{checksum:02X}\r\n"

    def make_gga(self, fix: NavSatFix) -> str:
        latitude, north_south = self.decimal_to_nmea(
            fix.latitude,
            is_latitude=True,
        )
        longitude, east_west = self.decimal_to_nmea(
            fix.longitude,
            is_latitude=False,
        )

        timestamp = datetime.now(timezone.utc).strftime("%H%M%S.00")

        # For VRS selection, the important fields are time and position.
        # Quality 1 means a valid autonomous GNSS fix.
        body = (
            f"GPGGA,{timestamp},"
            f"{latitude},{north_south},"
            f"{longitude},{east_west},"
            f"1,08,1.0,"
            f"{fix.altitude:.3f},M,"
            f"0.0,M,,"
        )

        return self.add_checksum(body)

    def make_request(self) -> bytes:
        credentials = f"{self.username}:{self.password}"
        authorization = base64.b64encode(credentials.encode("utf-8")).decode("ascii")

        request = (
            f"GET /{self.mountpoint} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Ntrip-Version: Ntrip/2.0\r\n"
            "User-Agent: NTRIP ros2-live-gga/1.0\r\n"
            f"Authorization: Basic {authorization}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )

        return request.encode("ascii")

    @staticmethod
    def read_response_headers(connection: socket.socket) -> bytes:
        received = bytearray()

        while b"\r\n\r\n" not in received:
            chunk = connection.recv(1)

            if not chunk:
                raise ConnectionError("Caster closed connection during handshake")

            received.extend(chunk)

            if len(received) > 16384:
                raise ConnectionError("NTRIP response headers too large")

        return bytes(received)

    @staticmethod
    def response_is_successful(headers: bytes) -> bool:
        first_line = headers.split(b"\r\n", 1)[0]

        return b"200 OK" in first_line or first_line.startswith(b"ICY 200")

    def get_latest_fix(self) -> NavSatFix | None:
        with self.position_lock:
            return self.latest_fix

    def connect_once(self) -> None:
        # Wait until the receiver has produced its own initial position.
        while self.running and rclpy.ok():
            fix = self.get_latest_fix()

            if fix is not None:
                break

            time.sleep(0.25)

        if not self.running or not rclpy.ok():
            return

        self.get_logger().info(
            f"Connecting to {self.host}:{self.port}/{self.mountpoint}"
        )

        with serial.Serial(
            port=self.serial_port,
            baudrate=self.serial_baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0,
            write_timeout=2.0,
        ) as receiver_serial:
            with socket.create_connection(
                (self.host, self.port),
                timeout=15.0,
            ) as caster:
                caster.settimeout(None)
                caster.sendall(self.make_request())

                headers = self.read_response_headers(caster)

                if not self.response_is_successful(headers):
                    first_line = headers.split(b"\r\n", 1)[0]
                    raise ConnectionError(
                        f"NTRIP connection rejected: "
                        f"{first_line.decode(errors='replace')}"
                    )

                self.get_logger().info("NTRIP connection established")

                next_gga_time = 0.0
                bytes_received = 0
                last_report_time = time.monotonic()

                while self.running and rclpy.ok():
                    now = time.monotonic()

                    if now >= next_gga_time:
                        fix = self.get_latest_fix()

                        if fix is not None:
                            gga = self.make_gga(fix)
                            caster.sendall(gga.encode("ascii"))
                            self.get_logger().debug(f"Sent GGA: {gga.strip()}")

                        next_gga_time = now + self.gga_interval

                    readable, _, _ = select.select(
                        [caster],
                        [],
                        [],
                        0.25,
                    )

                    if caster in readable:
                        rtcm = caster.recv(8192)

                        if not rtcm:
                            raise ConnectionError("NTRIP caster closed the connection")

                        receiver_serial.write(rtcm)
                        bytes_received += len(rtcm)

                    if now - last_report_time >= 10.0:
                        self.get_logger().info(
                            f"Received {bytes_received} RTCM bytes "
                            "during the last reporting period"
                        )
                        bytes_received = 0
                        last_report_time = now

    def connection_loop(self) -> None:
        while self.running and rclpy.ok():
            try:
                self.connect_once()
            except Exception as error:
                if self.running and rclpy.ok():
                    self.get_logger().error(f"NTRIP connection error: {error}")
                    time.sleep(self.reconnect_delay)

    def destroy_node(self) -> bool:
        self.running = False
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RosNtripClient()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
