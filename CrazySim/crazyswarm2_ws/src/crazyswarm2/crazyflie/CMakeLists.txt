cmake_minimum_required(VERSION 3.8)
project(crazyflie)

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)

# Install folders (Launch, Config, URDF) - Essential for Crazyswarm2
install(DIRECTORY
  launch
  config
  urdf
  DESTINATION share/${PROJECT_NAME}
)

# Install Python scripts - This is where crazyflie_server.py lives
install(PROGRAMS
  scripts/crazyflie_server.py
  scripts/vel_mux.py
  scripts/gui.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
