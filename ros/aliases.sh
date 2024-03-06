# shellcheck shell=sh

alias kg='killall -9 gazebo & killall -9 gzserver  & killall -9 gzclient'
alias kr='killall -9 roslaunch'

alias caktin='catkin'

# Isaac ROS developement
export ISAAC_ROS_REPO=$HOME/workspaces/isaac_ros-dev/
export ISAAC_ROS_WS=$HOME/workspaces/isaac_ros-dev/ros_ws/
alias cdw='cd ${ISAAC_ROS_WS:?}'
alias cdws='cd ${ISAAC_ROS_WS:?}/src'
alias run_isaac_dev='(cd ${ISAAC_ROS_REPO:?} && ./scripts/run_dev.sh ${ISAAC_ROS_WS})'

# Carter developement
export CARTER_DEV_REPO=$HOME/workspaces/carter-dev/
export CARTER_DEV_WS=$HOME/workspaces/carter-dev/ros_ws
alias cdc='cd ${CARTER_DEV_REPO:?}'
alias cdcs='cd ${CARTER_DEV_WS:?}/src'
alias run_carter_dev='(cd ${CARTER_DEV_REPO:?} && ./scripts/run_dev.sh ${CARTER_DEV_WS})'

ros2() {
    local args=()
    for arg in "$@"; do
        if [[ "$arg" == "t" ]]; then
            args+=("topic")
        elif [[ "$arg" == "n" ]]; then
            args+=("node")
        elif [[ "$arg" == "ls" ]]; then
            args+=("list")
        elif [[ "$arg" == "i" ]]; then
            args+=("info")
        else
            args+=("${arg}")
        fi
    done
    echo "Running command 'ros ${args[@]}'."
    command ros2 "${args[@]}"
}
