#!/bin/zsh

function source_ros() {
  [ -f /opt/ros/humble/setup.zsh ] && source /opt/ros/humble/setup.zsh
  source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.zsh
  eval "$(register-python-argcomplete3 ros2)"
  eval "$(register-python-argcomplete3 colcon)"
  eval "$(register-python-argcomplete ros2)"
  eval "$(register-python-argcomplete colcon)"
}
