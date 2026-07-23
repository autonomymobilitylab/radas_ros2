cmake_minimum_required(VERSION 3.8)
project(basler_ptp_config)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_srvs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(pylon_ros2_camera_interfaces REQUIRED)

add_executable(basler_ptp_configurator
  src/basler_ptp_configurator.cpp
)

target_include_directories(basler_ptp_configurator PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(basler_ptp_configurator
  rclcpp
  std_srvs
  sensor_msgs
  pylon_ros2_camera_interfaces
)

target_compile_features(basler_ptp_configurator PUBLIC cxx_std_17)

install(
  TARGETS basler_ptp_configurator
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()