#!/bin/bash

set -e

# Install bazelisk as bazel.
brew install bazelisk

# Install buildifier and buildozer.
version=v8.0.3
os=$(uname -s | tr '[:upper:]' '[:lower:]')
sudo mkdir -p /opt/bazel/tools
sudo wget https://github.com/bazelbuild/buildtools/releases/download/${version}/buildozer-${os}-amd64 -O /opt/bazel/tools/buildozer
sudo wget https://github.com/bazelbuild/buildtools/releases/download/${version}/buildifier-${os}-amd64 -O /opt/bazel/tools/buildifier

sudo chmod +x /opt/bazel/tools/buildozer
sudo chmod +x /opt/bazel/tools/buildifier
