#!/bin/bash

install_git_prompt() {
  # Install git prompt to add the git branch to the prompt.
  if [ -d ~/.bash-git-prompt ]; then
    echo "INFO: git-prompt already installed."
    git -C ~/.bash-git-prompt pull
  else
    echo "INFO: git-prompt not installed, installing."
    git clone https://github.com/magicmonty/bash-git-prompt.git ~/.bash-git-prompt --depth=1
  fi
}

install_vim_plug() {
  # Install the vim-plug plugin manager.
  if [ -f ~/.vim/autoload/plug.vim ]; then
    echo "INFO: vim-plug already installed."
    return
  fi
  echo "INFO: vim-plug not installed, installing."
  curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
      https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
}

install_vim_plugins() {
  echo "INFO: Installing vim plugins."
  vim -c "PlugInstall | qa"
}

source_bashrc_if_correct_user() {
  local line_to_add='if [ "$SSH_USER" = "lgulich" ]; then source "~/.${USER}_bashrc.bash"; fi'
  local target_bashrc="$HOME/.bashrc"

  if grep -qF -- "$line_to_add" "$target_bashrc" 2>/dev/null; then
    echo "INFO: Conditional source for lgulich already in $target_bashrc."
  else
    echo "INFO: Adding conditional source for lgulich to $target_bashrc."
    echo "$line_to_add" >> "$target_bashrc"
  fi
}

run_function_on_remote() {
    local func_name="$1"
    local remote_host="$2"
    echo "INFO: Running '$func_name' on '$remote_host'."
    ssh "${remote_host}" "$(typeset -f "$func_name"); $func_name"
}

set -e

remote=${1:?}

scp -r "${DOTFILES:?}/bash/bashrc.bash" "${remote}:~/.${USER}_bashrc.bash"
scp -r "${DOTFILES:?}/vim/minimal_vimrc.vim" "${remote}:~/.vimrc"

run_function_on_remote install_git_prompt "${remote}"
run_function_on_remote install_vim_plug "${remote}"
run_function_on_remote install_vim_plugins "${remote}"
run_function_on_remote source_bashrc_if_correct_user "${remote}"
