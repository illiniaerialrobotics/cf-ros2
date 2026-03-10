#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "### Starting cf-ros2 Setup for ECE484 ###"

echo "### Adding the Gazebo repository ### 
sudo apt update
sudo apt install curl lsb-release gnupg
sudo curl -sSL https://packages.osrfoundation.org/gazebo.gpg \
-o /usr/share/keyrings/gazebo-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/gazebo-archive-keyring.gpg] \
http://packages.osrfoundation.org/gazebo/ubuntu-stable \
$(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list
sudo apt update

# 1. Update and Install System Dependencies
echo "--> Installing system dependencies..."
sudo apt update && sudo apt install -y \
    build-essential cmake git curl lsb-release gnupg \
    python3-pip python3-venv python3-colcon-common-extensions \
    python3-rosdep python3-vcstool ros-humble-desktop \
    ros-humble-rclpy ros-humble-motion-capture-tracking \
    ros-humble-tf-transformations libusb-1.0-0-dev \
    libyaml-cpp-dev libboost-all-dev libeigen3-dev \
    libgz-sim7-dev libgz-transport12-dev libgz-msgs9-dev \
    libgz-plugin2-dev libgz-common5-dev libgz-math7-dev

# 2. Setup Python Virtual Environment
echo "--> Setting up Python virtual environment..."
if [ ! -d "venv_cf" ]; then
    python3 -m venv venv_cf
fi
source venv_cf/bin/activate

# Upgrade pip
pip install --upgrade pip

# 3. Setup Crazyflie Firmware
echo "--> Building crazyflie-firmware..."
cd CrazySim/crazyflie-firmware
pip install Jinja2
mkdir -p sitl_make/build
cd sitl_make/build
cmake ..
make all
cd ../../..

# 4. Install CFLib
echo "--> Installing crazyflie-lib-python (CFLib)..."
cd crazyflie-lib-python
# Uninstall existing to ensure clean slate
pip uninstall -y cflib || true
export SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0
pip install -e .
cd ../..

# 5. Setup Crazyswarm2 Workspace
echo "--> Building crazyswarm2 workspace..."
cd CrazySim/crazyswarm2_ws
# Install workspace-specific python deps
pip install catkin_pkg empy==3.3.4 lark "numpy<2.0" transforms3d

# Source ROS2 Humble before building
source /opt/ros/humble/setup.bash

# Build the workspace
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
cd ../..

echo "------------------------------------------------"
echo "SETUP COMPLETE!"
echo "To start working, remember to always:"
echo "1. Source your venv: source venv_cf/bin/activate"
echo "2. Source ROS: source /opt/ros/humble/setup.bash"
echo "3. Source the workspace: source CrazySim/crazyswarm2_ws/install/setup.bash"
echo "------------------------------------------------"