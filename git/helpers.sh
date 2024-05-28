# shellcheck shell=sh

git_clean_up_branches() {
  git fetch -p
  for branch in $(git for-each-ref --format '%(refname) %(upstream:track)' refs/heads | awk '$2 == "[gone]" {sub("refs/heads/", "", $1); print $1}')
  do
    git branch -D "$branch"
  done
}

git_go_to_repo_root() {
  cd "$(git rev-parse --show-toplevel || echo ".")" || exit 1
}

git_submodule_reset() {
  submodule_path=${1:-.}
  git submodule deinit -f ${submodule_path}
  git submodule update --recursive --init
}

git_submodule_bump() {
  git submodule update --recursive --remote
}

git_pull_with_stash() {
  git add .
  git stash
  git pull --rebase
  git stash apply
}
