#!/bin/sh

set -ex

curl -fLo "$script_dir"/vim/vim_plug/autoload/plug.vim --create-dirs \
  https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

