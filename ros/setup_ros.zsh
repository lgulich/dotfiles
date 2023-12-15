#!/bin/zsh

function source_ros() {
  [ -f /opt/ros/humble/setup.zsh ] && source /opt/ros/humble/setup.zsh
  source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.zsh
  export ROS_DOMAIN_ID=33
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  export CYCLONEDDS_URI=/home/lgulich/Documents/config/cyclone_unicast_profile.xml
}

# For isaac sim:
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/lgulich/.local/share/ov/pkg/isaac_sim-2023.1.0/exts/omni.isaac.ros2_bridge/humble/lib
#
function setup_ros_isaac_sim() {
  export ROS_DOMAIN_ID=0
  export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
  export FASTRTPS_DEFAULT_PROFILES_FILE=~/workspaces/IsaacSim-ros_workspaces/fastdds_profile.xml
}

function setup_ros_marmot() {
  local ip=$(getent hosts carter-v23-9.dyn.nvidia.com | awk '{ print $1 }')
  export ROS_DOMAIN_ID=0
  export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
  # export ROS_DISCOVERY_SERVER=$ip:11811
  # export FASTRTPS_DEFAULT_PROFILES_FILE=/home/lgulich/fastdds_profile.xml
}

function setup_ros_local() {
  # export ROS_DOMAIN_ID=0
  # export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
}

