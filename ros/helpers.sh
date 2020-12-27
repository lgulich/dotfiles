# shellcheck shell=sh

catkin_create_compile_commands() {
  cd "$(catkin locate --workspace "$(pwd)")" || exit 1

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

# Setup Clion for catkin metapackages. Use like so:
# $ update_clion_ws <you_metapackage_name>
update_clion_ws() {
  metapackage="$1"
  rm -rf ~/clion_ws/ && \
    python ~/Documents/editor_tools/init_clion.py -c ~/ -n ~/clion_ws -w ~/catkin_ws "$metapackage"
}
