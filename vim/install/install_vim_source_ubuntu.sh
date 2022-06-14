#!/bin/sh

set -e

sudo apt-get install -y \
  checkinstall \
  git \
  libatk1.0-dev \
  libcairo2-dev  \
  libgtk2.0-dev \
  liblua5.1-dev \
  libncurses5-dev \
  libperl-dev \
  libx11-dev \
  libxpm-dev \
  libxt-dev \
  lua5.1 \
  python-dev \
  python3-dev \
  ruby-dev

sudo apt-get remove -y \
  vim \
  vim-runtime \
  gvim

cd "$(mktemp -d)"
git clone https://github.com/vim/vim.git
cd vim
./configure \
  --with-features=huge \
  --enable-multibyte \
  --enable-pythoninterp=yes \
  --with-python-config-dir "$(python-config --configdir)" \
  --enable-perlinterp=yes \
  --enable-cscope \
  --prefix=/usr/local

make
sudo make install
