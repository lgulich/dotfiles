return {
  {
    'neovim/nvim-lspconfig',
    config = function()
      -- LSP keymaps
      vim.keymap.set('n', 'gd', vim.lsp.buf.definition, { silent = true })
      vim.keymap.set('n', 'gD', vim.lsp.buf.declaration, { silent = true })
      vim.keymap.set('n', 'gr', vim.lsp.buf.references, { silent = true })
      vim.keymap.set('n', 'gi', vim.lsp.buf.implementation, { silent = true })
      vim.keymap.set('n', 'K', vim.lsp.buf.hover, { silent = true })
      vim.keymap.set('n', '<C-k>', vim.lsp.buf.signature_help, { silent = true })
    end,
  },
  { 'hrsh7th/cmp-nvim-lsp' },
  { 'hrsh7th/cmp-buffer' },
  { 'hrsh7th/cmp-path' },
  { 'hrsh7th/cmp-cmdline' },
  { 'hrsh7th/nvim-cmp' },
}
