#!/bin/sh

set -e

sudo apt-get update
sudo apt-get install curl

cd "$(mktemp -d)"
curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim.appimage
chmod u+x nvim.appimage

./nvim.appimage --appimage-extract
./squashfs-root/AppRun --version

sudo rm -rf /squashfs-root
sudo mv squashfs-root /
sudo ln -fs /squashfs-root/AppRun /usr/bin/nvim
