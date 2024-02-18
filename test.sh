#!/bin/bash

set -ex

script_path=$(dirname "$0")
cd ${script_path}

docker run -it --entrypoint dotfiles/install.sh --workdir /root -v `realpath .`:/root/dotfiles ubuntu:22.04
