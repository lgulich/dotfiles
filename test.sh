#!/bin/bash

set -ex

script_path=$(dirname "$0")
cd ${script_path}

# Use a persistent cache directory for faster subsequent runs
cache_dir="/tmp/dotfiles-test-cache"
mkdir -p ${cache_dir}

# Sync dotfiles to cache directory (remove old cache and copy fresh)
rm -rf ${cache_dir}
mkdir -p ${cache_dir}
cp -a . ${cache_dir}/
rm -rf ${cache_dir}/generated ${cache_dir}/.git

# Check if Docker is available and working
if docker info > /dev/null 2>&1; then
  echo "Running test in Docker container..."
  docker run \
    --env DEBIAN_FRONTEND=noninteractive \
    --env TZ=UTC \
    --env HOME=/root \
    --entrypoint dotfiles/install.sh \
    --workdir /root \
    -v ${cache_dir}:/root/dotfiles \
    ubuntu:24.04
else
  echo "Docker not available, running test directly in cache directory..."
  export DEBIAN_FRONTEND=noninteractive
  export TZ=UTC
  cd ${cache_dir}
  ./install.sh
fi
