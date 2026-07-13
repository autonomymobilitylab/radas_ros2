#include <rclcpp/rclcpp.hpp>

#include <sensor_msgs/msg/point_cloud2.hpp>
#include <sensor_msgs/msg/point_field.hpp>

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>

namespace jt_correction
{

class JtPointCloudCorrector final : public rclcpp::Node
{
public:
  using PointCloud2 = sensor_msgs::msg::PointCloud2;
  using PointField = sensor_msgs::msg::PointField;

  explicit JtPointCloudCorrector(
    const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("jt_pointcloud_corrector", options)
  {
    load_transform_parameters();

    publisher_ = create_publisher<PointCloud2>(
      kOutputTopic,
      rclcpp::SensorDataQoS());

    subscription_ = create_subscription<PointCloud2>(
      kInputTopic,
      rclcpp::SensorDataQoS(),
      [this](PointCloud2::UniquePtr cloud) {
        point_cloud_callback(std::move(cloud));
      });

    RCLCPP_INFO(
      get_logger(),
      "JT point-cloud corrector started: %s -> %s, output frame: %s",
      kInputTopic,
      kOutputTopic,
      output_frame_.c_str());

    RCLCPP_INFO(
      get_logger(),
      "Translation: [%.6f, %.6f, %.6f]",
      tx_, ty_, tz_);

    RCLCPP_INFO(
      get_logger(),
      "Quaternion x/y/z/w: [%.6f, %.6f, %.6f, %.6f]",
      quaternion_x_,
      quaternion_y_,
      quaternion_z_,
      quaternion_w_);
  }

private:
  static constexpr const char * kInputTopic = "/lidar_points_jt";
  static constexpr const char * kOutputTopic =
    "/lidar_points_jt_corrected";

  struct XyzOffsets
  {
    std::uint32_t x;
    std::uint32_t y;
    std::uint32_t z;
  };

  void load_transform_parameters()
  {
    const double tx =
      declare_parameter<double>("translation.x", 0.0);
    const double ty =
      declare_parameter<double>("translation.y", 0.0);
    const double tz =
      declare_parameter<double>("translation.z", 0.0);

    double qx =
      declare_parameter<double>("rotation.x", 0.0);
    double qy =
      declare_parameter<double>("rotation.y", 0.0);
    double qz =
      declare_parameter<double>("rotation.z", 0.0);
    double qw =
      declare_parameter<double>("rotation.w", 1.0);

    output_frame_ =
      declare_parameter<std::string>(
      "output_frame",
      "lidar_jt_corrected");

    const double quaternion_norm =
      std::sqrt(qx * qx + qy * qy + qz * qz + qw * qw);

    if (!std::isfinite(quaternion_norm) ||
      quaternion_norm < 1.0e-12)
    {
      throw std::runtime_error(
              "Configured quaternion has zero or invalid magnitude");
    }

    qx /= quaternion_norm;
    qy /= quaternion_norm;
    qz /= quaternion_norm;
    qw /= quaternion_norm;

    quaternion_x_ = qx;
    quaternion_y_ = qy;
    quaternion_z_ = qz;
    quaternion_w_ = qw;

    tx_ = static_cast<float>(tx);
    ty_ = static_cast<float>(ty);
    tz_ = static_cast<float>(tz);

    /*
     * Quaternion-to-rotation-matrix conversion.
     *
     * Config quaternion order:
     *   x, y, z, w
     *
     * Applied transform:
     *   output_point = R * input_point + translation
     */
    const double xx = qx * qx;
    const double yy = qy * qy;
    const double zz = qz * qz;
    const double xy = qx * qy;
    const double xz = qx * qz;
    const double yz = qy * qz;
    const double wx = qw * qx;
    const double wy = qw * qy;
    const double wz = qw * qz;

    r00_ = static_cast<float>(1.0 - 2.0 * (yy + zz));
    r01_ = static_cast<float>(2.0 * (xy - wz));
    r02_ = static_cast<float>(2.0 * (xz + wy));

    r10_ = static_cast<float>(2.0 * (xy + wz));
    r11_ = static_cast<float>(1.0 - 2.0 * (xx + zz));
    r12_ = static_cast<float>(2.0 * (yz - wx));

    r20_ = static_cast<float>(2.0 * (xz - wy));
    r21_ = static_cast<float>(2.0 * (yz + wx));
    r22_ = static_cast<float>(1.0 - 2.0 * (xx + yy));
  }

  static std::optional<XyzOffsets> find_xyz_offsets(
    const PointCloud2 & cloud)
  {
    std::optional<std::uint32_t> x_offset;
    std::optional<std::uint32_t> y_offset;
    std::optional<std::uint32_t> z_offset;

    for (const PointField & field : cloud.fields) {
      if (field.name != "x" &&
        field.name != "y" &&
        field.name != "z")
      {
        continue;
      }

      if (field.datatype != PointField::FLOAT32 ||
        field.count != 1U)
      {
        return std::nullopt;
      }

      if (field.name == "x") {
        x_offset = field.offset;
      } else if (field.name == "y") {
        y_offset = field.offset;
      } else {
        z_offset = field.offset;
      }
    }

    if (!x_offset || !y_offset || !z_offset) {
      return std::nullopt;
    }

    return XyzOffsets{
      *x_offset,
      *y_offset,
      *z_offset
    };
  }

  static bool layout_is_valid(
    const PointCloud2 & cloud,
    const XyzOffsets & offsets)
  {
    const std::uint32_t largest_offset =
      std::max({offsets.x, offsets.y, offsets.z});

    if (largest_offset + sizeof(float) > cloud.point_step) {
      return false;
    }

    const std::size_t required_row_size =
      static_cast<std::size_t>(cloud.width) *
      static_cast<std::size_t>(cloud.point_step);

    if (cloud.row_step < required_row_size) {
      return false;
    }

    const std::size_t required_data_size =
      static_cast<std::size_t>(cloud.height) *
      static_cast<std::size_t>(cloud.row_step);

    return cloud.data.size() >= required_data_size;
  }

  inline void transform_point(
    std::uint8_t * point,
    const XyzOffsets & offsets) const noexcept
  {
    float x;
    float y;
    float z;

    /*
     * memcpy is intentional. PointCloud2 field addresses are not
     * guaranteed to be aligned suitably for float pointer access.
     */
    std::memcpy(
      &x,
      point + offsets.x,
      sizeof(float));

    std::memcpy(
      &y,
      point + offsets.y,
      sizeof(float));

    std::memcpy(
      &z,
      point + offsets.z,
      sizeof(float));

    /*
     * Preserve invalid points. This also prevents a translation from
     * turning an all-NaN invalid point into a partially finite point.
     */
    if (!std::isfinite(x) ||
      !std::isfinite(y) ||
      !std::isfinite(z))
    {
      return;
    }

    const float corrected_x =
      r00_ * x + r01_ * y + r02_ * z + tx_;

    const float corrected_y =
      r10_ * x + r11_ * y + r12_ * z + ty_;

    const float corrected_z =
      r20_ * x + r21_ * y + r22_ * z + tz_;

    std::memcpy(
      point + offsets.x,
      &corrected_x,
      sizeof(float));

    std::memcpy(
      point + offsets.y,
      &corrected_y,
      sizeof(float));

    std::memcpy(
      point + offsets.z,
      &corrected_z,
      sizeof(float));
  }

  void point_cloud_callback(PointCloud2::UniquePtr cloud)
  {
    if (!cloud) {
      return;
    }

    if (cloud->is_bigendian) {
      RCLCPP_ERROR_THROTTLE(
        get_logger(),
        *get_clock(),
        5000,
        "Big-endian PointCloud2 messages are not supported");

      return;
    }

    if (cloud->width == 0U ||
      cloud->height == 0U ||
      cloud->data.empty())
    {
      cloud->header.frame_id = output_frame_;
      publisher_->publish(std::move(cloud));
      return;
    }

    /*
     * Resolve the offsets from the current message. The fields array is
     * tiny compared with the point buffer, so this validation has
     * negligible cost and remains correct if the input layout changes.
     */
    const std::optional<XyzOffsets> offsets =
      find_xyz_offsets(*cloud);

    if (!offsets) {
      RCLCPP_ERROR_THROTTLE(
        get_logger(),
        *get_clock(),
        5000,
        "Input cloud must contain x, y and z fields of type FLOAT32");

      return;
    }

    if (!layout_is_valid(*cloud, *offsets)) {
      RCLCPP_ERROR_THROTTLE(
        get_logger(),
        *get_clock(),
        5000,
        "Input PointCloud2 has an invalid point or row layout");

      return;
    }

    /*
     * Respect row_step so organized point clouds and row padding are
     * handled correctly. For ordinary LiDAR clouds, height is usually 1.
     */
    for (std::uint32_t row = 0; row < cloud->height; ++row) {
      std::uint8_t * point =
        cloud->data.data() +
        static_cast<std::size_t>(row) * cloud->row_step;

      for (std::uint32_t column = 0;
        column < cloud->width;
        ++column)
      {
        transform_point(point, *offsets);
        point += cloud->point_step;
      }
    }

    /*
     * XYZ now physically uses output_frame_ coordinates, so changing
     * frame_id is valid.
     */
    cloud->header.frame_id = output_frame_;

    publisher_->publish(std::move(cloud));
  }

  rclcpp::Publisher<PointCloud2>::SharedPtr publisher_;
  rclcpp::Subscription<PointCloud2>::SharedPtr subscription_;

  std::string output_frame_;

  float tx_{0.0F};
  float ty_{0.0F};
  float tz_{0.0F};

  float r00_{1.0F};
  float r01_{0.0F};
  float r02_{0.0F};

  float r10_{0.0F};
  float r11_{1.0F};
  float r12_{0.0F};

  float r20_{0.0F};
  float r21_{0.0F};
  float r22_{1.0F};

  double quaternion_x_{0.0};
  double quaternion_y_{0.0};
  double quaternion_z_{0.0};
  double quaternion_w_{1.0};
};

}  // namespace jt_correction

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  try {
    const auto node =
      std::make_shared<jt_correction::JtPointCloudCorrector>();

    rclcpp::spin(node);
  } catch (const std::exception & exception) {
    RCLCPP_FATAL(
      rclcpp::get_logger("jt_pointcloud_corrector"),
      "Failed to start node: %s",
      exception.what());

    rclcpp::shutdown();
    return 1;
  }

  rclcpp::shutdown();
  return 0;
}