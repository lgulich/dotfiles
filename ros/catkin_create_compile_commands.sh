#!/bin/sh

set -e

cd "$(catkin locate --workspace "$(pwd)")" || exit 1

# shellcheck disable=SC2086
catkin build -c -DCMAKE_EXPORT_COMPILE_COMMANDS=1 $1

cat ./build/**/compile_commands.json > compile_commands.json \
  && sed -i -e ':a;N;$!ba;s/\]\n*\[/,/g' compile_commands.json

compdb -p . list > compile_commands_extended.json

rm ~/compile_commands.json || true
cp compile_commands_extended.json ~/compile_commands.json
