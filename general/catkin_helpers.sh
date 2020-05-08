#!/bin/sh -e

create_catkin_compile_commands() {
  cd "$(catkin locate --workspace "$(pwd)")"

  # shellcheck disable=SC2086
  catkin build -c -DCMAKE_EXPORT_COMPILE_COMMANDS=1 $1

  concatenated="build/compile_commands.json"

  echo "[" > $concatenated

  for d in build/*; do
    file="$d/compile_commands.json"

    if [ -f "$file" ]; then
      # shellcheck disable=SC2002
      cat "$file" | sed '1d;$d' >> "$concatenated"
      echo "," >> $concatenated
    fi
  done

  echo "]" >> "$concatenated"

  vim "$concatenated" -c "Autoformat | x"

  cp build/compile_commands.json ~/compile_commands.json
}
