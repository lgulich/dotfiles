#!/bin/sh

# Setup Clion for catkin metapackages. Use like so:
# $ update_clion_ws.sh <you_metapackage_name>

set -e

metapackage="$1"
rm -rf ~/clion_ws/ && \
  python ~/Code/editor_tools/init_clion.py -c ~/ -n ~/clion_ws -w ~/catkin_ws "$metapackage"
