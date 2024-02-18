vim.cmd('source $DOTFILES/vim/config/commands.vim')
vim.cmd('source $DOTFILES/vim/config/set.vim')
vim.cmd('source $DOTFILES/vim/config/keymap.vim')
vim.cmd('source $DOTFILES/vim/config/plug.vim')
vim.cmd('source $DOTFILES/vim/config/plugins.vim')

-- LSP Setup (move to own file when becomes too big)
-- ClangD
require('lspconfig').clangd.setup{
  filetypes = {'c', 'cpp', 'cxx', 'cc'}
}

require('lspconfig').rust_analyzer.setup{}
require('lspconfig').pyright.setup{}
require('lspconfig').tsserver.setup{}
