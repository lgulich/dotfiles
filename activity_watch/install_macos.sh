#!/bin/sh
set -ex

tmpdir="$(mktemp -d)"
cd ${tmpdir}

release=$(curl -s https://api.github.com/repos/ActivityWatch/activitywatch/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')

wget https://github.com/ActivityWatch/activitywatch/releases/download/${release}/activitywatch-${release}-macos-x86_64.dmg

open ${tmpdir}/activitywatch-${release}-macos-x86_64.dmg
