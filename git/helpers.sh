# shellcheck shell=sh

git_clean_up_branches(){
  git fetch -p
  for branch in $(git for-each-ref --format '%(refname) %(upstream:track)' refs/heads | awk '$2 == "[gone]" {sub("refs/heads/", "", $1); print $1}')
  do
    git branch -D "$branch"
  done
}

git_go_to_repo_root() {
  cd "$(git rev-parse --show-toplevel || echo ".")" || exit 1
}
