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

# Oh my zsh configuration
export ZSH="${HOME}/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"
plugins=(
  vi-mode
  git
  fzf
  zsh-autosuggestions
  ssh-agent
  command-not-found
  1password
  ag
  bazel
  colorize
  colored-man-pages
  docker
  docker-compose
  zsh-syntax-highlighting
)
source "${ZSH}"/oh-my-zsh.sh

# Enable autocomplete for bash autocomplete definitions.
autoload -U +X compinit && compinit
autoload -U +X bashcompinit && bashcompinit

# Enable autocomplete for one-password
eval "$(op completion zsh)"; compdef _op op

# Often used directories.
export DOTFILES=~/Code/dotfiles

# Default UNIX env variables:
export PATH="/usr/lib/ccache:${PATH}" # ccache for faster builds.
export PATH="${DOTFILES:?}/generated/bin:${PATH}"
export VISUAL=nvim
export EDITOR=nvim
export BROWSER=brave-browser

# SSL
export OPENSSL_ROOT_DIR=/usr/local/opt/openssl@1.1

# Source files generated by dotfiles
source "${DOTFILES:?}"/generated/sources.sh

# Load fzf fuzzyfinder.
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
export FZF_DEFAULT_COMMAND='fd --type f --hidden'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"

# Bazel autocomplete, caches bazel's options:
zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path ~/.zsh/cache

# Directory used for DAZEL cache
# export DAZEL_CACHE_ROOT=/media/lgulich/dazel-cache

# Load OSMO
export OSMO_PATH="/home/lgulich/Code/osmo"
export PATH=$PATH:$OSMO_PATH
export ISAAC_DEV_BAZEL=dazel
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/home/lgulich/.local/lib/python3.8/site_packages/tensorrt"
[ -f /home/lgulich/Code/osmo/osmo/autocomplete.bash ] && source '/home/lgulich/Code/osmo/osmo/autocomplete.bash'

# History setup
HISTSIZE=10000000
SAVEHIST=10000000
PROMPT_COMMAND='history -a'
HISTTIMEFORMAT="%F %T "
HISTORY_IGNORE="(ls|pwd|exit)*"
setopt EXTENDED_HISTORY      # Write the history file in the ':start:elapsed;command' format.
setopt INC_APPEND_HISTORY    # Write to the history file immediately, not when the shell exits.
setopt SHARE_HISTORY         # Share history between all sessions.
setopt HIST_IGNORE_DUPS      # Do not record an event that was just recorded again.
setopt HIST_IGNORE_ALL_DUPS  # Delete an old recorded event if a new event is a duplicate.
setopt HIST_IGNORE_SPACE     # Do not record an event starting with a space.
setopt HIST_SAVE_NO_DUPS     # Do not write a duplicate event to the history file.
setopt HIST_VERIFY           # Do not execute immediately upon history expansion.
setopt APPEND_HISTORY        # append to history file (Default)
setopt HIST_NO_STORE         # Don't store history commands
setopt HIST_REDUCE_BLANKS    # Remove superfluous blanks from each command line being added to the history.
HIST_STAMPS="yyyy-mm-dd"

eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
eval "$(atuin init zsh --disable-up-arrow)"
# Has to follow after atuin init.
ZSH_AUTOSUGGEST_STRATEGY=(history completion)
