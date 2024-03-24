

install_pre_commit_config() {
  target_path=${1:?}
  cp ${DOTFILES:?}/linters/config/clang-format ${target_path}/.clang-format
  cp ${DOTFILES:?}/linters/config/pre-commit-config.yaml ${target_path}/.pre-commit-config.yaml
  cp ${DOTFILES:?}/linters/config/pylintrc ${target_path}/.pylintrc
  cp ${DOTFILES:?}/linters/config/yamlfmt.yaml ${target_path}/.yamlfmt.yaml
  cp ${DOTFILES:?}/linters/config/yapf.style ${target_path}/.yapf.style
}
