#!/bin/sh

env_file="${1:?}"
cmd="${2:?}"
. "$env_file"
exec /usr/bin/env -i "$SHELL" -c ". $env_file; $cmd"
