#!/bin/bash

set -ex

export DOTFILES=~/dotfiles

cd "${DOTFILES}"

# Find the installers and run them iteratively.
find . -name "install.darwin.*" -mindepth 2 | while read install_script ; do sh -c "${install_script}" ; done

echo "Succesfully installed all dotfiles programs."

