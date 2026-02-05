return {
  -- Auto-save
  {
    'okuuva/auto-save.nvim',
    event = { 'InsertLeave', 'TextChanged' },
    opts = {},
  },

  -- Formatting
  {
    'stevearc/conform.nvim',
    event = { 'BufWritePre' },
    cmd = { 'ConformInfo' },
    keys = {
      { '<F3>', function() require('conform').format({ async = true }) end, desc = 'Format buffer' },
    },
    opts = {
      formatters_by_ft = {
        lua = { 'stylua' },
        python = { 'black' },
        javascript = { 'prettier' },
        typescript = { 'prettier' },
        json = { 'prettier' },
        yaml = { 'prettier' },
        markdown = { 'prettier' },
        cpp = { 'clang-format' },
        c = { 'clang-format' },
        rust = { 'rustfmt' },
      },
      format_on_save = {
        timeout_ms = 500,
        lsp_fallback = true,
      },
    },
  },

  -- File explorer
  {
    'nvim-tree/nvim-tree.lua',
    dependencies = { 'nvim-tree/nvim-web-devicons' },
    keys = {
      { '<C-n>', '<cmd>NvimTreeToggle<cr>', desc = 'Toggle file tree' },
      { '<leader>f', '<cmd>NvimTreeFindFile<cr>', desc = 'Find file in tree' },
    },
    opts = {
      view = { width = 35 },
      renderer = { icons = { show = { git = true } } },
    },
  },

  -- Fuzzy finder
  {
    'nvim-telescope/telescope.nvim',
    branch = '0.1.x',
    dependencies = {
      'nvim-lua/plenary.nvim',
      { 'nvim-telescope/telescope-fzf-native.nvim', build = 'make' },
    },
    keys = {
      { '<C-p>', '<cmd>Telescope find_files<cr>', desc = 'Find files' },
      { '<leader>fg', '<cmd>Telescope live_grep<cr>', desc = 'Live grep' },
      { '<leader>fb', '<cmd>Telescope buffers<cr>', desc = 'Find buffers' },
      { '<leader>fh', '<cmd>Telescope help_tags<cr>', desc = 'Help tags' },
      { '<leader>fr', '<cmd>Telescope oldfiles<cr>', desc = 'Recent files' },
      { 'gr', '<cmd>Telescope lsp_references<cr>', desc = 'LSP references' },
    },
    config = function()
      local telescope = require('telescope')
      telescope.setup({
        defaults = {
          file_ignore_patterns = { 'node_modules', '.git/' },
        },
      })
      telescope.load_extension('fzf')
    end,
  },

  -- Git integration
  {
    'lewis6991/gitsigns.nvim',
    event = { 'BufReadPre', 'BufNewFile' },
    opts = {
      current_line_blame = true,
      current_line_blame_opts = {
        delay = 500,
      },
      on_attach = function(bufnr)
        local gs = package.loaded.gitsigns
        local map = function(mode, l, r, desc)
          vim.keymap.set(mode, l, r, { buffer = bufnr, desc = desc })
        end
        map('n', ']h', gs.next_hunk, 'Next hunk')
        map('n', '[h', gs.prev_hunk, 'Prev hunk')
        map('n', '<leader>hs', gs.stage_hunk, 'Stage hunk')
        map('n', '<leader>hr', gs.reset_hunk, 'Reset hunk')
        map('n', '<leader>hp', gs.preview_hunk, 'Preview hunk')
        map('n', '<leader>hb', gs.blame_line, 'Blame line')
      end,
    },
  },

  -- Git commands
  {
    'tpope/vim-fugitive',
    cmd = { 'Git', 'Gvdiff', 'Gdiffsplit' },
    keys = {
      { '<leader>gd', '<cmd>Gvdiff<cr>', desc = 'Git diff' },
      { 'dgh', '<cmd>diffget //2<cr>', desc = 'Diffget left' },
      { 'dgl', '<cmd>diffget //3<cr>', desc = 'Diffget right' },
    },
  },

  -- Surround
  {
    'kylechui/nvim-surround',
    version = '*',
    event = 'VeryLazy',
    opts = {},
  },

  -- Statusline
  {
    'nvim-lualine/lualine.nvim',
    dependencies = { 'nvim-tree/nvim-web-devicons' },
    opts = {
      options = {
        theme = 'onedark',
        component_separators = '|',
        section_separators = '',
      },
    },
  },

  -- Subword motion (CamelCase, snake_case)
  {
    'chrisgrieser/nvim-spider',
    keys = {
      { 'w', "<cmd>lua require('spider').motion('w')<cr>", mode = { 'n', 'o', 'x' }, desc = 'Spider w' },
      { 'e', "<cmd>lua require('spider').motion('e')<cr>", mode = { 'n', 'o', 'x' }, desc = 'Spider e' },
      { 'b', "<cmd>lua require('spider').motion('b')<cr>", mode = { 'n', 'o', 'x' }, desc = 'Spider b' },
    },
  },

  -- Repeat plugin commands
  { 'tpope/vim-repeat', event = 'VeryLazy' },

  -- Case-preserving substitution
  { 'tpope/vim-abolish', event = 'VeryLazy' },

  -- Activity tracking
  { 'ActivityWatch/aw-watcher-vim' },
}
