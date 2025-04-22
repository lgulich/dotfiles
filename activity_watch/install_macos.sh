#!/bin/sh
set -e

tmpdir="$(mktemp -d)"
cd ${tmpdir}

release='v0.13.2'

wget https://github.com/ActivityWatch/activitywatch/releases/download/${release}/activitywatch-${release}-macos-x86_64.dmg

open ${tmpdir}/activitywatch-${release}-macos-x86_64.dmg
