function cd() {
  builtin cd "$1"  && ls -a
}

function add_sudo() {
  BUFFER="sudo "$BUFFER
  zle end-of-line
}
