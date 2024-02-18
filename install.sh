#!/bin/bash

install_dependencies_macos(){
  python3 -m pip install dotfile-manager
}

install_dependencies_linux(){
  if ! command -v sudo &>/dev/null; then
      apt-get update && apt-get install -y sudo
  fi
  sudo apt-get update
  sudo apt-get install -y python3 python3-pip git software-properties-common curl wget
  python3 -m pip install dotfile-manager
  export PATH="~/.local/bin:$PATH"
}

set -e

os="$(uname -s)"

if [ "$os" == "Darwin" ]; then
  install_dependencies_macos
elif [ "$os" == "Linux" ]; then
  install_dependencies_linux
fi

if [ "$1" == "--only-deps" ]; then
  exit 0
fi

script_path=$(dirname "$0")
export DOTFILES="$script_path"
dotfile_manager install -v
dotfile_manager setup
