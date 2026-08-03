import argparse
import os

import numpy as np
import open3d as o3d

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2 as pc2


class PointCloudSaver(Node):
    def __init__(self, save_directory: str, lidar_name: str):
        super().__init__("pointcloud_saver")

        self.save_dir = save_directory
        self.lidar_name = lidar_name
        self.point_topic = f"/lidar_points_{self.lidar_name}"
        self.topic_dir = os.path.join(self.save_dir, self.lidar_name)
        os.makedirs(self.topic_dir, exist_ok=True)

        self.subscription = self.create_subscription(
            PointCloud2,
            self.point_topic,
            self.pointcloud_callback,
            10,
        )
        self.count = 0

    def pointcloud_callback(self, msg):
        points = pc2.read_points_numpy(
            msg,
            field_names=("x", "y", "z"),
            skip_nans=True,
        )

        xyz = np.asarray(points, dtype=np.float64).reshape(-1, 3)

        out_pcd = o3d.geometry.PointCloud()
        out_pcd.points = o3d.utility.Vector3dVector(xyz)

        filename = f"cloud_{self.count:06d}.pcd"
        filepath = os.path.join(self.topic_dir, filename)

        suc = o3d.io.write_point_cloud(
            filepath,
            out_pcd,
            write_ascii=False,
            compressed=True,
        )

        if suc:
            self.get_logger().info(f"Saved point cloud to {filepath}")
        else:
            self.get_logger().error(f"Failed to save point cloud to {filepath}")

        self.count += 1


def parse_args():
    parser = argparse.ArgumentParser(
        description="Save ROS2 PointCloud2 messages as PCD files."
    )
    parser.add_argument(
        "--save-directory",
        default="/data/pointclouds",
        help="Directory to save point clouds.",
    )
    parser.add_argument(
        "--lidar-name",
        default="xt",
        help="LiDAR name (used to determine the topic and output subdirectory).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    rclpy.init()
    node = PointCloudSaver(
        save_directory=args.save_directory,
        lidar_name=args.lidar_name,
    )

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
