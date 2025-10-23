#!/bin/bash

set -e

# create tmp dir
tmpdir="$(mktemp -d)"
cd ${tmpdir}

wget https://github.com/bazelbuild/bazelisk/releases/download/v1.27.0/bazelisk-amd64.deb
sudo apt-get install -y ./bazelisk-amd64.deb

# Verify installation
bazelisk --version
bazel --version
