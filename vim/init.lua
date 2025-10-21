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
require('lspconfig').ts_ls.setup{}

require('remote-sshfs').setup({
  connections = {
    sshfs_args = {
      "-o reconnect",
      "-o ConnectTimeout=5",
      "-o cache=yes",
      "-o kernel_cache",
      "-o auto_cache",
    },
  },
})
require('telescope').load_extension 'remote-sshfs'

require('supermaven-nvim').setup{}
