cmake_minimum_required(VERSION 3.8)
project(jt_correction)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(eigen3_cmake_module REQUIRED)
find_package(Eigen3 REQUIRED)

add_executable(
  jt_pointcloud_corrector
  src/jt_pointcloud_corrector.cpp
)

ament_target_dependencies(
  jt_pointcloud_corrector
  rclcpp
  sensor_msgs
)

target_link_libraries(
  jt_pointcloud_corrector
  Eigen3::Eigen
)

target_compile_features(
  jt_pointcloud_corrector
  PUBLIC
  cxx_std_17
)

target_compile_options(
  jt_pointcloud_corrector
  PRIVATE
  -O3
)

install(
  TARGETS jt_pointcloud_corrector
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
