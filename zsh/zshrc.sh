# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

SCRIPT_DIR="$(dirname -- "$0")"

export VISUAL=vim
export EDITOR=vim

# Oh my zsh configuration
export ZSH="$SCRIPT_DIR"/plugins/ohmyzsh
ZSH_THEME="powerlevel10k/powerlevel10k"
ZSH_CUSTOM="$SCRIPT_DIR"
plugins=(
  vi-mode
  git
  zsh-autosuggestions
)
source "$ZSH"/oh-my-zsh.sh

# Source other configurations
source "$SCRIPT_DIR"/util.sh
source "$SCRIPT_DIR"/aliases.sh
source "$SCRIPT_DIR"/keybindings.sh

# Load Powerlevel10k config. To reconfigure run `p10k configure`
[[ ! -f "$SCRIPT_DIR"/p10k.zsh ]] || source "$SCRIPT_DIR"/p10k.zsh
