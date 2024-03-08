#!/bin/bash

set -e

script_path=$(dirname $(realpath $0))
cd ${script_path}

# Install MesloLGS Nerd Font
mkdir -p ~/.fonts
cp ../fonts/* ~/.fonts
