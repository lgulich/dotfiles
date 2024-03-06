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

require('gp').setup{
    openai_api_key = os.getenv("NVCF_API_KEY"),
    openai_api_endpoint = 'https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/8f4118ba-60a8-4e6b-8574-e38a4067a4a3',
}
