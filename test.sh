#!/bin/bash

set -ex

script_path=$(dirname "$0")
cd ${script_path}

# Use a persistent cache directory for faster subsequent runs
cache_dir="/tmp/dotfiles-test-cache"
mkdir -p ${cache_dir}

# Sync dotfiles to cache directory (only copy changed files, delete extra files)
rsync -a --delete --exclude='generated/' --exclude='.git/' . ${cache_dir}/

docker run \
  --env DEBIAN_FRONTEND=noninteractive \
  --env TZ=UTC \
  --env HOME=/root \
  --entrypoint dotfiles/install.sh \
  --workdir /root \
  -v ${cache_dir}:/root/dotfiles \
  ubuntu:24.04
