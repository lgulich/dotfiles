#!/bin/sh

set -e

# Install MesloLGS Nerd Font
mkdir -p ~/.fonts
SCRIPT_PATH=$(dirname $(realpath -s $0))
cp "${SCRIPT_PATH}"/fonts/* ~/.fonts
