# shellcheck shell=zsh

cd_and_ls() {
  cd "$1" && ls
}

edit_dotfile() {
  local script_path="${(%):-%x}"
  local script_dir="$(dirname -- "$script_path")"
  local repo_root=$(git -C "${script_dir}" rev-parse --show-toplevel)

  # Add new config options here, path is from root of dotfiles repo.
  declare -A options
  options[alacritty]="alacritty/alacritty.yml"
  options[i3]="i3/config"
  options[tmux]="tmux/tmux.conf"
  options[vim-plugins]="vim/vimrc.vim"
  options[vim-vanilla]="vim/vimrc.vim"
  options[zsh]="zsh/zshrc.zsh"

  # We convert the array to a newline separated list which can be read by dmenu.
  options_string=""
  for key in "${(@k)options}"; do
    options_string="${options_string}${key}\n"
  done

  local choice=$(echo -e "${options_string}" | dmenu)
  [ "$?" = 0 ] && "${EDITOR}" "${repo_root}/${options[$choice]}"
}
