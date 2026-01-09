#!/bin/bash

install_dependencies_macos(){
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source $HOME/.local/bin/env
}

install_dependencies_linux(){
  if ! command -v sudo &>/dev/null; then
      apt-get update && apt-get install -y sudo
  fi
  sudo apt-get update
  sudo apt-get install -y git software-properties-common curl wget unzip
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source $HOME/.local/bin/env
}

set -e

os="$(uname -s)"

if [ "${os}" == "Darwin" ]; then
  install_dependencies_macos
elif [ "${os}" == "Linux" ]; then
  install_dependencies_linux
fi

if [ "$1" == "--only-deps" ]; then
  exit 0
fi

script_path=$(dirname "$0")
export DOTFILES="$script_path"
uvx dotfile-manager install --verbose
uvx dotfile-manager setup
