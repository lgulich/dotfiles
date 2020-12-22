#!/bin/sh

set -ex

sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main"
  > /etc/apt/sources.list.d/ros-latest.list'

curl -sSL 'http://keyserver.ubuntu.com/pks/lookup?op=get&search=0xC1CF6E31E6BADE8868B172B4F42ED6FBAB17C654' \
| sudo apt-key add -

sudo apt-get update
sudo apt-get install -y \
  ros-melodic-desktop-full \
  python-rosdep \
  python-rosinstall \
  python-rosinstall-generator \
  python-wstool \
  build-essential \
  python-catkin-tools

sudo rosdep init || true
rosdep update
