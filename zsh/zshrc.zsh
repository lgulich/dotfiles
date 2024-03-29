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
if [ -f /home/lgulich/Code/osmo/osmo/autocomplete.bash ]; then . '/home/lgulich/Code/osmo/osmo/autocomplete.bash'; fi

# History setup
PROMPT_COMMAND='history -a'
HISTTIMEFORMAT="%F %T "

# Load google cloud stuff
if [ -f '/home/lgulich/Code/google-cloud-sdk/path.zsh.inc' ]; then . '/home/lgulich/Code/google-cloud-sdk/path.zsh.inc'; fi
if [ -f '/home/lgulich/Code/google-cloud-sdk/completion.zsh.inc' ]; then . '/home/lgulich/Code/google-cloud-sdk/completion.zsh.inc'; fi

eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
