#!/bin/bash

set -e

# Create tmp dir.
tmpdir="$(mktemp -d)"
cd ${tmpdir}

# Detect architecture.
arch=$(dpkg --print-architecture)
wget https://github.com/bazelbuild/bazelisk/releases/download/v1.27.0/bazelisk-${arch}.deb
sudo apt-get install -y ./bazelisk-${arch}.deb

# Verify installation
bazelisk --version
bazel --version
