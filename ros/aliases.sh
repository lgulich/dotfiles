# shellcheck shell=sh

alias kg='killall -9 gazebo & killall -9 gzserver  & killall -9 gzclient'
alias kr='killall -9 roslaunch'

alias caktin='catkin'

# ROS developement
export ISAAC_ROS_WS=$HOME/workspaces/isaac_ros-dev/ros_ws/
export ISAAC_ROS_REPO=$HOME/workspaces/isaac_ros-dev/
alias cdws='cd ${ISAAC_ROS_WS:?}'
alias cdwss='cd ${ISAAC_ROS_WS:?}/src'
alias run_isaac_dev='(cd ${ISAAC_ROS_WS:?}/src/isaac_ros_common/scripts && ./run_dev.sh ${ISAAC_ROS_WS})'

# Carter developement
export CARTER_DEV_REPO=$HOME/workspaces/carter-dev/
export CARTER_DEV_WS=$HOME/workspaces/carter-dev/ros_ws
alias cdc='cd ${CARTER_DEV_REPO:?}'
alias cdcs='cd ${CARTER_DEV_WS:?}/src'
alias run_carter_dev='(cd ${CARTER_DEV_REPO:?} && ./scripts/run_dev.sh ${CARTER_DEV_REPO})'
