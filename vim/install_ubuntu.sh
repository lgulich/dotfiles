#!/bin/sh

set -ex

"${DOTFILES}"/vim/install/install_neovim_ubuntu.sh
"${DOTFILES}"/vim/install/install_plugins.sh

