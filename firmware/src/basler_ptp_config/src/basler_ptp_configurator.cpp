#include <chrono>
#include <cstdint>
#include <iomanip>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "std_srvs/srv/set_bool.hpp"

#include "pylon_ros2_camera_interfaces/srv/get_ptp_status.hpp"
#include "pylon_ros2_camera_interfaces/srv/issue_scheduled_action_command.hpp"
#include "pylon_ros2_camera_interfaces/srv/set_action_trigger_configuration.hpp"
#include "pylon_ros2_camera_interfaces/srv/set_integer_value.hpp"
#include "pylon_ros2_camera_interfaces/srv/set_roi.hpp"

using namespace std::chrono_literals;

class BaslerPtpConfigurator : public rclcpp::Node
{
public:
  BaslerPtpConfigurator()
      : Node("basler_ptp_configurator")
  {
    positions_ = declare_parameter<std::vector<std::string>>(
        "positions", {"left", "right", "middle"});

    broadcast_address_ =
        declare_parameter<std::string>("broadcast_address", "192.168.1.255");

    device_key_ = declare_parameter<int64_t>("device_key", 1);
    group_key_ = declare_parameter<int64_t>("group_key", 1);
    group_mask_ = declare_parameter<int64_t>("group_mask", 1);

    action_delay_ns_ =
        declare_parameter<int64_t>("action_delay_ns", 100000000);

    action_sender_ =
        declare_parameter<std::string>("action_sender", "middle");

    service_timeout_ms_ =
        declare_parameter<int>("service_timeout_ms", 5000);
  }

  bool run()
  {
    bool all_ok = true;

    for (const auto &position : positions_)
    {
      RCLCPP_INFO(
          get_logger(), "Configuring camera '%s'...", position.c_str());

      all_ok &= configure_camera(position);
    }

    if (!all_ok)
    {
      RCLCPP_ERROR(
          get_logger(),
          "At least one camera configuration failed.");

      return false;
    }

    for (const auto &position : positions_)
    {
      all_ok &= request_ptp_status(position);
    }

    if (!all_ok)
    {
      RCLCPP_ERROR(
          get_logger(),
          "At least one PTP status request failed.");

      return false;
    }

    RCLCPP_INFO(
        get_logger(),
        "All cameras configured. Sending scheduled action command.");

    all_ok &= issue_scheduled_action(action_sender_);

    if (!all_ok)
    {
      RCLCPP_ERROR(
          get_logger(),
          "Scheduled action command failed.");

      return false;
    }

    RCLCPP_INFO(
        get_logger(),
        "Scheduled action command service call completed.");

    return true;
  }

private:
  std::string camera_base(const std::string &position) const
  {
    return "/Basler_" + position + "/pylon_ros2_camera_node";
  }

  template <typename ServiceT>
  bool wait_for_service(
      const typename rclcpp::Client<ServiceT>::SharedPtr &client,
      const std::string &service_name)
  {
    const auto timeout = std::chrono::milliseconds(service_timeout_ms_);

    if (!client->wait_for_service(timeout))
    {
      RCLCPP_ERROR(
          get_logger(), "Service unavailable: %s", service_name.c_str());
      return false;
    }
    return true;
  }

  template <typename ServiceT>
  bool call_service(
      const std::string &service_name,
      const std::shared_ptr<typename ServiceT::Request> &request)
  {
    auto client = create_client<ServiceT>(service_name);

    if (!wait_for_service<ServiceT>(client, service_name))
    {
      return false;
    }

    auto future = client->async_send_request(request);
    const auto timeout = std::chrono::milliseconds(service_timeout_ms_);

    const auto result =
        rclcpp::spin_until_future_complete(get_node_base_interface(), future, timeout);

    if (result != rclcpp::FutureReturnCode::SUCCESS)
    {
      RCLCPP_ERROR(
          get_logger(), "Service call failed or timed out: %s",
          service_name.c_str());
      return false;
    }

    const auto response = future.get();
    if (!response)
    {
      RCLCPP_ERROR(
          get_logger(), "Empty response from service: %s",
          service_name.c_str());
      return false;
    }

    RCLCPP_INFO(
        get_logger(), "Service call completed: %s", service_name.c_str());
    return true;
  }

  bool set_integer(
      const std::string &base,
      const std::string &service_suffix,
      int64_t value)
  {
    using Service = pylon_ros2_camera_interfaces::srv::SetIntegerValue;

    auto request = std::make_shared<Service::Request>();
    request->value = value;

    return call_service<Service>(base + "/" + service_suffix, request);
  }

  bool set_bool(
      const std::string &base,
      const std::string &service_suffix,
      bool value)
  {
    using Service = std_srvs::srv::SetBool;

    auto request = std::make_shared<Service::Request>();
    request->data = value;

    return call_service<Service>(base + "/" + service_suffix, request);
  }

  bool set_roi(const std::string &base)
  {
    using Service = pylon_ros2_camera_interfaces::srv::SetROI;

    auto request = std::make_shared<Service::Request>();
    request->target_roi.x_offset = 0;
    request->target_roi.y_offset = 0;
    request->target_roi.height = 1200;
    request->target_roi.width = 1920;
    request->target_roi.do_rectify = false;

    return call_service<Service>(base + "/set_roi", request);
  }

  bool set_action_trigger_configuration(const std::string &base)
  {
    using Service =
        pylon_ros2_camera_interfaces::srv::SetActionTriggerConfiguration;

    auto request = std::make_shared<Service::Request>();

    request->action_device_key =
        static_cast<int64_t>(device_key_);

    request->action_group_key =
        static_cast<int64_t>(group_key_);

    request->action_group_mask =
        static_cast<int64_t>(group_mask_);

    RCLCPP_INFO(
        get_logger(),
        "Configuring action trigger on %s: "
        "device_key=0x%08x, group_key=0x%08x, group_mask=0x%08x",
        base.c_str(),
        static_cast<uint32_t>(device_key_),
        static_cast<uint32_t>(group_key_),
        static_cast<uint32_t>(group_mask_));

    return call_service<Service>(
        base + "/set_action_trigger_configuration",
        request);
  }

  bool configure_camera(const std::string &position)
  {
    const std::string base = camera_base(position);
    bool ok = true;

    ok &= set_bool(base, "enable_ptp_management_protocol", true);
    ok &= set_integer(base, "set_ptp_priority", 127);
    ok &= set_integer(base, "set_ptp_profile", 1);
    ok &= set_integer(base, "set_ptp_network_mode", 2);

    ok &= set_bool(base, "enable_two_step_operation", false);
    ok &= set_bool(base, "enable_ptp", true);
    ok &= set_roi(base);

    // Trigger configuration
    ok &= set_action_trigger_configuration(base);
    // 0 = FrameStart
    ok &= set_integer(base, "set_trigger_selector", 0);

    // 5 = Action1
    ok &= set_integer(base, "set_trigger_source", 5);

    // Enable trigger mode
    ok &= set_bool(base, "set_trigger_mode", true);

    if (ok)
    {
      RCLCPP_INFO(
          get_logger(), "Camera '%s' configured successfully.",
          position.c_str());
    }
    else
    {
      RCLCPP_ERROR(
          get_logger(), "Configuration failed for camera '%s'.",
          position.c_str());
    }

    return ok;
  }

  bool request_ptp_status(const std::string &position)
  {
    using Service = pylon_ros2_camera_interfaces::srv::GetPtpStatus;

    const std::string service_name =
        camera_base(position) + "/get_ptp_status";

    auto request = std::make_shared<Service::Request>();
    const bool ok = call_service<Service>(service_name, request);

    if (ok)
    {
      RCLCPP_INFO(
          get_logger(),
          "PTP status response received for camera '%s'.",
          position.c_str());
    }

    return ok;
  }

  bool issue_scheduled_action(const std::string &sender_position)
  {
    using Service =
        pylon_ros2_camera_interfaces::srv::IssueScheduledActionCommand;

    const std::string service_name =
        camera_base(sender_position) + "/issue_scheduled_action_command";

    auto request = std::make_shared<Service::Request>();
    request->device_key = static_cast<int32_t>(device_key_);
    request->group_key = static_cast<int32_t>(group_key_);
    request->group_mask = static_cast<uint32_t>(group_mask_);
    request->action_time_ns_from_current_timestamp =
        static_cast<uint64_t>(action_delay_ns_);
    request->broadcast_address = broadcast_address_;

    std::ostringstream details;
    details << "Sending scheduled action through camera '" << sender_position
            << "': device_key=0x" << std::hex << static_cast<uint32_t>(device_key_)
            << ", group_key=0x" << static_cast<uint32_t>(group_key_)
            << ", group_mask=0x" << static_cast<uint32_t>(group_mask_)
            << std::dec << ", delay_ns=" << action_delay_ns_
            << ", broadcast=" << broadcast_address_;

    RCLCPP_INFO(get_logger(), "%s", details.str().c_str());

    return call_service<Service>(service_name, request);
  }

  std::vector<std::string> positions_;
  std::string broadcast_address_;
  int64_t device_key_;
  int64_t group_key_;
  int64_t group_mask_;
  int64_t action_delay_ns_;
  std::string action_sender_;
  int service_timeout_ms_;
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<BaslerPtpConfigurator>();
  const bool success = node->run();

  rclcpp::shutdown();
  return success ? 0 : 1;
}