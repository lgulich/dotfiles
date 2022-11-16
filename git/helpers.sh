# shellcheck shell=sh

git_publish_branch(){
  git push --set-upstream origin "$(git rev-parse --abbrev-ref HEAD)"
}

git_reset_to_origin(){
  git fetch origin
  git reset --hard origin/"$(git rev-parse --abbrev-ref HEAD)"
}

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

git_ammend_to() {
  git_ammend_to.sh $1
}
