#!/bin/sh
set -ex

tmpdir="$(mktemp -d)"
cd ${tmpdir}

release=$(curl -s https://api.github.com/repos/ActivityWatch/activitywatch/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')

wget https://github.com/ActivityWatch/activitywatch/releases/download/${release}/activitywatch-${release}-linux-x86_64.zip

unzip activitywatch-${release}-linux-x86_64.zip
mkdir -p ~/Code/installed/
cp -r ${tmpdir}/activitywatch ~/Code/installed/
