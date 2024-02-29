# shellcheck shell=sh

cd_and_ls() {
  "cd" "$1" && ls
}

show_largest_files() {
  sudo du -sh .[^.]* | sort -rh | head -n ${1:-10}
}
