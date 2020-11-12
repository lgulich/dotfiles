#!/bin/sh

set -ex

sudo add-apt-repository ppa:jonathonf/vim
sudo apt-get update
sudo apt-get install -y vim
