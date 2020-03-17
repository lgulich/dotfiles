SCRIPT_DIR="$(dirname -- "$0")"

export VISUAL=vim
export EDITOR=vim

# Oh my zsh configuration
export ZSH="$SCRIPT_DIR"/plugins/ohmyzsh
ZSH_THEME="robbyrussell"
plugins=(
  vi-mode
  git
)
source "$ZSH"/oh-my-zsh.sh

# Source other configurations
source "$SCRIPT_DIR"/util.sh
source "$SCRIPT_DIR"/aliases.sh
source "$SCRIPT_DIR"/keybindings.sh
source "$SCRIPT_DIR"/prompt.sh
