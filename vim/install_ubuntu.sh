#!/bin/sh

set -ex

"${DOTFILES}"/vim/install/install_vim_source_ubuntu.sh
"${DOTFILES}"/vim/install/install_vim_plug.sh
"${DOTFILES}"/vim/install/install_plugins.sh

