#!/bin/sh -ex

sudo apt-get install -y \
  checkinstall \
  git \
  libatk1.0-dev \
  libbonoboui2-dev \
  libcairo2-dev  \
  libgnome2-dev \
  libgnomeui-dev \
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

sudo apt-get remove \
  vim \
  vim-runtime \
  gvim

cd "$(mktemp)"
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
sudo checkinstall
