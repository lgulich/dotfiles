function cd() {
  builtin cd "$1" && ls -a
}

function add_sudo() {
  BUFFER="sudo "$BUFFER
  zle end-of-line
}

function edit_last_command() {
  BUFFER="fc"
  zle accept-line
}

function go_up_one_folder() {
  BUFFER="cd .."
  zle accept-line
}

function go_to_home() {
  BUFFER="cd ~/"
  zle accept-line
}

function go_to_git_root() {
  BUFFER="cd $(git rev-parse --show-toplevel || echo ".")"
  zle accept-line
}
