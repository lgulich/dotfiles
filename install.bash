#!/bin/bash

set -ex

OS="${1:?}"

if [ "${OS}" ==  "--ubuntu" ]; then
  cd "${DOTFILES:?}"
  sudo apt-get update
  # Find the installers and run them iteratively.
  find . -name "install.ubuntu.*" -mindepth 2 \
    | while read -r install_script; do
        sh -c "${install_script}" ;
      done
elif [ "${OS}" ==  "--darwin" ]; then
  cd "${DOTFILES:?}"
  brew update
  # Find the installers and run them iteratively.
  find . -name "install.darwin.*" -mindepth 2 \
    | while read -r install_script; do
        sh -c "${install_script}" ;
      done
fi

echo "Succesfully installed all dotfiles topics."
