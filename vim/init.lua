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

require('llm').setup({
  -- model = "bigcode/starcoderbase", -- can be a model ID or an http(s) endpoint
  -- tokenizer = {
  --   repository = "bigcode/starcoderbase",
  -- },
  model = "http://0.0.0.0:8000/api/generate/",
  tokenizer = nil,
  context_window = 8192, -- max number of tokens for the context window
  tokens_to_clear = { "<|endoftext|>" }, -- tokens to remove from the model's output
  -- parameters that are added to the request body
  query_params = {
    max_new_tokens = 60,
    temperature = 0.2,
    top_p = 0.95,
    stop_tokens = nil,
  },
  -- set this if the model supports fill in the middle
  fim = {
    enabled = true,
    prefix = "<fim_prefix>",
    middle = "<fim_middle>",
    suffix = "<fim_suffix>",
  },
  debounce_ms = 150,
  accept_keymap = "<Tab>",
  dismiss_keymap = "<S-Tab>",
  tls_skip_verify_insecure = false,
  -- lsp = {
    -- bin_path = "/home/lgulich/Code/llm-ls/target/release/llm-ls",
    -- version = "0.2.1",
  -- },
  enable_suggestions_on_startup = true,
  enable_suggestions_on_files = "*",
})

