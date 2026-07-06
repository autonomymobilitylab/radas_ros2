import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import argparse


class ImageSaver(Node):
    def __init__(self, save_directory: str, camera_name: str):
        super().__init__("image_saver")
        self.bridge = CvBridge()

        self.save_dir = save_directory
        self.camera_name = camera_name

        self.image_topic = f"/{self.camera_name}/pylon_ros2_camera_node/image_raw"
        self.topic_dir = os.path.join(self.save_dir, self.camera_name)
        os.makedirs(self.topic_dir, exist_ok=True)

        self.subscription = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            10,
        )
        self.count = 0

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="rgb8")
        filename = f"image_{self.count:06d}.png"
        filepath = os.path.join(self.topic_dir, filename)
        suc = cv2.imwrite(filepath, cv_image)

        if suc:
            self.get_logger().info(f"Saved image: {filepath}")
        else:
            self.get_logger().error(f"Failed to save image: {filepath}")
        self.count += 1


def parse_args():
    parser = argparse.ArgumentParser(description="Save ROS2 image messages to disk.")
    parser.add_argument(
        "--save-directory",
        default="/data/images",
        help="Directory to save images.",
    )
    parser.add_argument(
        "--camera-name",
        default="Basler_middle",
        help="Camera name (used to determine the topic and output subdirectory).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    rclpy.init()
    node = ImageSaver(
        save_directory=args.save_directory,
        camera_name=args.camera_name,
    )

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
