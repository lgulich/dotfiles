#!/bin/sh

set -e

# CoC.vim needs node.js >=12.12
curl -sL install-node.now.sh/lts | sudo bash

vim +PlugInstall +qall
