# shellcheck shell=zsh

# Load .profile
[ -f ~/.profile ] && source ~/.profile

# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

script_dir="$(dirname -- "$0")"

export VISUAL=vim
export EDITOR=vim

# Oh my zsh configuration
# export ZSH="$script_dir"/ohmyzsh
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"
# ZSH_CUSTOM="$script_dir"
plugins=(
  vi-mode
  git
  zsh-autosuggestions
)
source "$ZSH"/oh-my-zsh.sh

# Load custom helpers
source "$script_dir"/general_helpers.sh
source "$script_dir"/catkin_helpers.sh
source "$script_dir"/git_helpers.sh

# Source other configurations
source "$script_dir"/aliases.sh
source "$script_dir"/keybindings.zsh

# Load Powerlevel10k config. To reconfigure run `p10k configure`
[[ ! -f "$script_dir"/p10k.zsh ]] || source "$script_dir"/p10k.zsh

# Keymap to exit vi-insert-mode.
bindkey -e jk vi-cmd-mode 

# Load fzf fuzzyfinder.
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

export CXX=/usr/bin/g++-8

