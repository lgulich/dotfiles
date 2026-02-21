# shellcheck shell=sh

alias kg='killall -9 gazebo & killall -9 gzserver  & killall -9 gzclient'
alias kr='killall -9 roslaunch'

alias caktin='catkin'

# Isaac ROS developement
export ISAAC_DIR=/home/lgulich/workspaces/isaac
export ISAAC_ROS_WS=/home/lgulich/workspaces/isaac/ros_ws

alias cdw='cd ${ISAAC_DIR:?}'
alias cdws='cd ${ISAAC_DIR:?}/src'
alias run_isaac_dev='${ISAAC_ROS_REPO:?}/scripts/run_dev.sh -d ${ISAAC_ROS_REPO}'


ros() {
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
    echo "Running command 'ros2 ${args[@]}'."
    command ros2 "${args[@]}"
}
