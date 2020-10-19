# shellcheck shell=zsh

# Run tmux if exists.
if command -v tmux>/dev/null; then
	[ -z "$TMUX" ] && exec tmux
else
	echo "tmux not installed, could not autostart tmux."
fi

# Load .profile
[ -f ~/.profile ] && source ~/.profile

# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

export VISUAL=vim
export EDITOR=vim
export DOTFILES=~/dotfiles

# Oh my zsh configuration
export ZSH="${HOME}/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"
plugins=(
  vi-mode
  git
  zsh-autosuggestions
)
source "${ZSH}"/oh-my-zsh.sh

# Load custom helpers.
source "${DOTFILES}"/git/git_helpers.sh
source "${DOTFILES}"/ros/catkin_helpers.sh
source "${DOTFILES}"/zsh/general_helpers.zsh

# Custom aliases.
source "${DOTFILES}"/git/aliases.sh
source "${DOTFILES}"/ros/aliases.sh
source "${DOTFILES}"/zsh/aliases.sh

# Custom keybindings.
source "${DOTFILES}"/zsh/keybindings.zsh

# Load Powerlevel10k config. To reconfigure run `p10k configure`
[[ ! -f "${DOTFILES}"/zsh/p10k.zsh ]] || source "${DOTFILES}"/zsh/p10k.zsh

# Load fzf fuzzyfinder.
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Use g++9 as default.
export CXX=/usr/bin/g++-9

export COMPP_CORE_PATH=~/compp_core

# Use ccache for faster builds
export PATH="/usr/lib/ccache:$PATH"

# Load ROS.
[ -f /opt/ros/melodic/setup.zsh ] && source /opt/ros/melodic/setup.zsh
