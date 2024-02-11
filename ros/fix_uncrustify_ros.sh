#!/bin/bash

# Fix all c/c++ files in a directory (recursively) using the ROS configuration

set -e

path=${1:?}
find ${path} -type f \( -name "*.cpp" -o -name "*.hpp" \) -print0 | \
    xargs -0 -I {} uncrustify -c /opt/ros/humble/lib/python3.10/site-packages/ament_uncrustify/configuration/ament_code_style.cfg --no-backup -l CPP {}
