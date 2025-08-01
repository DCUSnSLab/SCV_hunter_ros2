cmake_minimum_required(VERSION 3.5)
project(hunter_base)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

find_package(hunter_msgs REQUIRED)
find_package(ugv_sdk REQUIRED)
add_subdirectory(ascent)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)
include_directories(
  include
)


set(DEPENDENCIES
  "geometry_msgs"
  "nav_msgs"
  "rclcpp"
  "std_msgs"
  "tf2"
  "tf2_ros"
  "hunter_msgs"
  "sensor_msgs"
  "tf2_geometry_msgs"
)


add_executable(hunter_base_node 
    src/hunter_base_ros.cpp
    src/hunter_base_node.cpp
    src/bicycle_model.cpp)
target_link_libraries(hunter_base_node ugv_sdk ${dependencies} ascent)
ament_target_dependencies(hunter_base_node rclcpp tf2 tf2_ros std_msgs nav_msgs sensor_msgs hunter_msgs tf2_geometry_msgs ${dependencies})

add_executable(velocity_extractor_node
    src/velocity_extractor_node.cpp)
ament_target_dependencies(velocity_extractor_node rclcpp std_msgs hunter_msgs)

install(TARGETS hunter_base_node velocity_extractor_node
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}/)

# install(DIRECTORY ascent
#   DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # uncomment the line when a copyright and license is not present in all source files
  #set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # uncomment the line when this package is not in a git repo
  #set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
