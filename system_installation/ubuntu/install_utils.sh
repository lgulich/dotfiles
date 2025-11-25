#!/bin/sh

set -e

sudo apt-get install -y \
    cmake \
    curl \
    fd-find \
    nodejs \
    python3 \
    python3-pip

mkdir -p ~/.local/bin
ln -s $(which fdfind) ~/.local/bin/fd

/home/linuxbrew/.linuxbrew/bin/brew install \
  fzf \
  go
