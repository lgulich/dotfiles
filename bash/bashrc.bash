# ~/.bashrc: executed by bash(1) for non-login shells.
# se /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# History setup.
HISTCONTROL=ignoreboth # ignore duplicates and lines starting with space
shopt -s histappend # Append to the history file
PROMPT_COMMAND="history -a;$PROMPT_COMMAND" # Write history immediately
HISTSIZE=10000000
HISTFILESIZE=10000000

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
#shopt -s globstar

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
#force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
	# We have color support; assume it's compliant with Ecma-48
	# (ISO/IEC-6429). (Lack of such support is extremely rare, and such
	# a case would tend to support setf rather than setaf.)
	color_prompt=yes
    else
	color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    #alias dir='dir --color=auto'
    #alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# colored GCC warnings and errors
#export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

# some more ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# Add an "alert" alias for long running commands.  Use like so:
#   sleep 10; alert
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

[ -f ~/.fzf.bash ] && source ~/.fzf.bash

EDITOR=vim

function find_content {
        search_path=${1:?}
        pattern=${2:?}
        find ${search_path} -type f -exec grep -Hn "${pattern}" {} +
}

function find_file {
        search_path=${1:?}
        pattern=${2:?}
        find ${search_path} -type f -name "${pattern}"
}

# Git
alias ga='git add'
alias gb='git branch'
alias gc='git commit'
alias gca='git commit --amend'
alias gch='git checkout'
alias gd='git diff --color'
alias gf='git fetch'
alias gl='git log --oneline'
alias gp='git push'
alias gpf='git push --force'
alias gpr='git pull --rebase'
alias grc='git rebase --continue'
alias gs='git status'
alias nah='git reset --hard && git clean -df;'

function git_submodule_reset() {
  submodule_path=${1:-.}
  git submodule deinit -f ${submodule_path}
  git submodule update --recursive --init --jobs 20
}

function git_submodule_bump() {
  submodule_path=${1:-.}
  git submodule deinit -f ${submodule_path}
  git submodule update --recursive --remote --jobs 20
}

function git_clean_up_branches() {
  git fetch -p
  for branch in $(git for-each-ref --format '%(refname) %(upstream:track)' refs/heads | awk '$2 == "[gone]" {sub("refs/heads/", "", $1); print $1}'); do
    git branch -D "$branch"
  done
}

function serve_file() {
  file_path="$(realpath ${1:?})"
  file_parentdir="$(dirname ${file_path})"
  file_basename="$(basename ${file_path})"

  ip=$(hostname -I | awk '{print $1}')
  port=8005
  echo "See file at: 'http://${ip}:${port}/${file_basename}'"
  python3 -m http.server ${port} --directory ${file_parentdir}
}

# Autocomplete with up key.
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# Colcon
function colcon_test_packages_select {
  package=${1:?}
  if [ -n "$2" ]; then
    # Test only tests matching regex pattern.
    pattern=${2:?}
    echo "Testing only '${pattern}' in package '${package}'."
    colcon test \
      --return-code-on-test-failure \
      --event-handlers console_direct+ \
      --packages-select ${package} \
      --ctest-args -R ${pattern}
  else
    echo "Testing entire package '${package}'."
    # Test entire package.
    colcon test \
      --return-code-on-test-failure \
      --event-handlers console_direct+ \
      --packages-select ${package}
  fi
}
alias cb='colcon build --symlink-install --continue-on-error --packages-up-to'
alias cbs='colcon build --symlink-install --packages-select'
alias ct='colcon test --return-code-on-test-failure --packages-up-to'
alias cts='colcon_test_packages_select'
alias cts_show='colcon test --ctest-args --show-only --packages-select'
alias src='source /workspaces/isaac_ros-dev/install/setup.bash'
alias cbi='colcon build --continue-on-error --packages-up-to'

# Carter
export ISAAC_REPO='/mnt/nova_ssd/workspaces/isaac-lgulich'
export ISAAC_WS="${ISAAC_REPO:?}/ros_ws/"
export CONFIG_CONTAINER_NAME_SUFFIX="${CONFIG_CONTAINER_NAME_SUFFIX}-lgulich"
export DOCKER_ARGS=(
  "-e CYCLONEDDS_URI=/usr/local/share/middleware_profiles/cyclone_unicast_profile.xml"
  "-v `realpath ~/.bashrc`:/home/admin/.bashrc"
)
alias cdlg="cd ${ISAAC_WS}/src"
alias run_dev='${ISAAC_REPO:?}/scripts/run_dev.sh -d ${ISAAC_REPO:?}'

[[ -f /opt/ros/humble/setup.bash ]] && source /opt/ros/humble/setup.bash
[[ -f ~/.bash-preexec.sh ]] && source ~/.bash-preexec.sh
eval "$(atuin init bash)"
. "$HOME/.cargo/env"

source /opt/ros/humble/setup.bash
source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash
