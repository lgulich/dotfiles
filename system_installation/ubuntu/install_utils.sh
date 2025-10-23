#!/bin/sh

set -e

sudo apt-get install -y \
    cmake \
    curl \
    nodejs \
    python3 \
    python3-pip

/home/linuxbrew/.linuxbrew/bin/brew install go
