#!/bin/sh

set -ex

cd "$(mktemp -d)"
wget -O atom-amd64.deb https://atom.io/download/deb
sudo apt-get install ./atom-amd64.deb
