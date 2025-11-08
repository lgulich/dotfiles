vim.cmd('source $DOTFILES/vim/config/commands.vim')
vim.cmd('source $DOTFILES/vim/config/set.vim')
vim.cmd('source $DOTFILES/vim/config/keymap.vim')
vim.cmd('source $DOTFILES/vim/config/plug.vim')
vim.cmd('source $DOTFILES/vim/config/plugins.vim')

-- LSP Setup (move to own file when becomes too big).
-- ClangD
vim.lsp.config.clangd = {
  cmd = { 'clangd' },
  filetypes = { 'c', 'cpp', 'cxx', 'cc' },
  root_markers = { '.clangd', '.clang-tidy', '.clang-format', 'compile_commands.json', 'compile_flags.txt', 'configure.ac', '.git' },
}

vim.lsp.config.rust_analyzer = {
  cmd = { 'rust-analyzer' },
  filetypes = { 'rust' },
  root_markers = { 'Cargo.toml', 'rust-project.json' },
}

vim.lsp.config.pyright = {
  cmd = { 'pyright-langserver', '--stdio' },
  filetypes = { 'python' },
  root_markers = { 'pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt', 'Pipfile', 'pyrightconfig.json' },
}

vim.lsp.config.ts_ls = {
  cmd = { 'typescript-language-server', '--stdio' },
  filetypes = { 'javascript', 'javascriptreact', 'javascript.jsx', 'typescript', 'typescriptreact', 'typescript.tsx' },
  root_markers = { 'package.json', 'tsconfig.json', 'jsconfig.json', '.git' },
}

vim.lsp.enable({ 'clangd', 'rust_analyzer', 'pyright', 'ts_ls' })

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
