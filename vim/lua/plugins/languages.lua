return {
  -- C/C++
  {
    'drmikehenry/vim-headerguard',
    ft = { 'cpp', 'c' },
    config = function()
      vim.cmd([[
        function! g:HeaderguardName()
          let prefix = 'NVIDIA_ISAAC'
          let project_name = expand('%:p:gs@.*sdk/\(.*\)/.*@\1@g')
          let project_name = substitute(project_name, '[^0-9a-zA-Z_]', '_', 'g')
          let project_name = toupper(project_name)
          let file_name = toupper(expand('%:t:gs/[^0-9a-zA-Z_]/_/g'))
          return prefix . "_" . project_name . "_" . file_name . "_"
        endfunction

        function! g:HeaderguardLine3()
          return "#endif  // " . g:HeaderguardName() . ""
        endfunction
      ]])
    end,
  },

  {
    'lgulich/toggle-header-source.vim',
    ft = { 'cpp', 'c', 'h', 'hpp' },
    keys = {
      { '<F5>', ':call ToggleHeaderSource()<CR>', desc = 'Toggle header/source' },
    },
  },

  { 'bfrg/vim-cpp-modern', ft = { 'cpp', 'c' } },

  -- Rust
  { 'rust-lang/rust.vim', ft = 'rust' },

  -- Latex
  {
    'lervag/vimtex',
    ft = { 'tex', 'latex' },
    config = function()
      vim.g.tex_flavor = 'latex'
      vim.g.vimtex_view_method = 'zathura'
      vim.g.vimtex_quickfix_mode = 0
      vim.opt.conceallevel = 0
      vim.g.tex_conceal = 'abdmg'
    end,
  },
  { 'rhysd/vim-grammarous', ft = { 'tex', 'latex', 'markdown' } },

  -- Bazel
  { 'google/vim-maktaba', ft = { 'bzl', 'BUILD' } },
  { 'bazelbuild/vim-bazel', ft = { 'bzl', 'BUILD' }, dependencies = { 'google/vim-maktaba' } },

  -- Documentation
  { 'godlygeek/tabular', cmd = 'Tabularize' },
  { 'preservim/vim-markdown', ft = 'markdown', dependencies = { 'godlygeek/tabular' } },
  { 'habamax/vim-rst', ft = 'rst' },

  -- Protobuf
  { 'uarun/vim-protobuf', ft = 'proto' },

  -- Beancount
  { 'nathangrigg/vim-beancount', ft = 'beancount' },

}
