#!/bin/sh

set -e

# Use python3.12 explicitly to ensure apt_pkg is available
sudo python3.12 /usr/bin/add-apt-repository ppa:aslatter/ppa -y
sudo apt-get update
sudo apt-get install -y alacritty
