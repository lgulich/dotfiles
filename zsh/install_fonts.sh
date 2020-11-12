#!/bin/sh

set -ex

# Install MesloLGS Nerd Font
mkdir -p ~/.fonts
cp "${DOTFILES}"/zsh/fonts/* ~/.fonts
