# cf-ros2
This is the software stack for autonomous CrazyFlie flight used in ECE484@UIUC. It is based off CrazySim, which uses Gazebo and crazyswarm2. 

## Set-up

### Preliminary installations
This stack has been tested on Ubuntu 22.04 + ROS2 Humble + Gazebo Garden. Other configurations may work but will not be supported officially as of SP26. 

If you are on a Windows/MacOS, you can access Ubuntu 22.04 via WSL2 and VMs. 

- Instructions for installing ROS2 Humble are [here](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html).
- Instructions for installing Gazebo Garden are [here](https://gazebosim.org/docs/garden/install_ubuntu/).

### Further setup

In `CrazySim/crazyflie-firmware`, run the following commands: 
```
sudo apt install cmake build-essential
pip install Jinja2
mkdir -p sitl_make/build && cd $_
cmake ..
make all
```

You can now load a CrazyFlie and a track in the simulator with the following command:
```
bash tools/crazyflie-simulation/simulator_files/gazebo/launch/sitl_singleagent.sh -m crazyflie -x <x-coord> -y <y-coord> -w <TRACK>
```
For example, to load a CrazyFlie at the default position (1, -1) and the Circle track, run: 
```
bash tools/crazyflie-simulation/simulator_files/gazebo/launch/sitl_singleagent.sh -m crazyflie -w circle
```

To setup crazyswarm2, run the following in `crazyswarm2_ws`:
```
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
pip install "numpy<2.0"
```

In `crazyswarm2_ws/src/crazyswarm2/crazyflie/config/crazyflies.yaml` add the following under *robots* and *robot_types*: 
```
robots:
  cf_1:
      enabled: true
      uri: udp://0.0.0.0:19850
      initial_position: [0.0, 0.0, 0.0]
      type: cf_sim

robot_types:
  cf_sim:
    motion_capture:
      tracking: "vendor"
    big_quad: false
    firmware_logging:
      enabled: true
      default_topics:
        pose:
          frequency: 1
```
If you have any other robots in `crazyflies.yaml`, either delete them or disable them. 

## Getting you started
Controllers can/should go in `CrazySim\crazyswarm2_ws\src\crazyswarm2\crazyflie_examples\crazyflie_examples\controllers\`. You are given a waypoint controller file to start off.

As you add more controllers, you can add them as entry points in `CrazySim\crazyswarm2_ws\src\crazyswarm2\crazyflie_examples\setup.cfg`. 

To test the waypoint navigator on the Circle track, run the following commands in three different terminals: 
```
# Terminal 1
bash tools/crazyflie-simulation/simulator_files/gazebo/launch/sitl_singleagent.sh -m crazyflie -w circle
# Terminal 2
ros2 launch crazyflie launch.py backend:=cflib
# Terminal 3
ros2 run crazyflie_examples waypoint_follower
```  

## Updates
This repository will be continuously updated. More controllers and tracks may be provided. Any majors edits will be listed below. 
