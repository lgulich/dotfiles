#!/bin/bash

set -ex

export DOTFILES=~/dotfiles

cd "${DOTFILES}"

sudo apt-get update

# Find the installers and run them iteratively.
find . -name "install.ubuntu.*" -mindepth 2 | while read install_script ; do sh -c "${install_script}" ; done

