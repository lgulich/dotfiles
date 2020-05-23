# shellcheck shell=sh

cd_and_ls() {
  cd "$1" && ls || exit 1
}
