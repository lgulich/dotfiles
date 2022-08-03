vim.cmd('source $DOTFILES/vim/config/commands.vim')
vim.cmd('source $DOTFILES/vim/config/set.vim')
vim.cmd('source $DOTFILES/vim/config/keymap.vim')
vim.cmd('source $DOTFILES/vim/config/plug.vim')
vim.cmd('source $DOTFILES/vim/config/plugins.vim')

-- LSP Setup (move to own file when becomes to big)
require('lspconfig').clangd.setup{}
