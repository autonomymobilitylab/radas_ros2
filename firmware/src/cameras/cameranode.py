import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os

class ImageSaver(Node):
    def __init__(self):
        super().__init__('image_saver')
        self.bridge = CvBridge()
        
        self.declare_parameter('save_directory', '/data/images')
        self.declare_parameter('camera_name', 'Basler_middle')
        
        self.save_dir = self.get_parameter('save_directory').value
        self.camera_name = self.get_parameter('camera_name').value
        self.image_topic = f"/{self.camera_name}/pylon_ros2_camera_node/image_raw"
        self.topic_dir = os.path.join(self.save_dir, self.camera_name)
        os.makedirs(self.topic_dir, exist_ok=True)
        
        self.subscription = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            10
        )
        self.count = 0
        
    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        filename = f"image_{self.count:06d}.png"
        filepath = os.path.join(self.topic_dir, filename)
        suc = cv2.imwrite(filepath, cv_image)
        if suc:
            self.get_logger().info(f"Saved image: {filepath}")
        else:
            self.get_logger().error(f"Failed to save image: {filepath}")
        self.count += 1
        
def main():
    rclpy.init()
    node = ImageSaver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    
if __name__ == '__main__':
    main()