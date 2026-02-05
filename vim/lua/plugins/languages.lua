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
    config = function()
      vim.keymap.set('', '<F5>', ':call ToggleHeaderSource()<CR>')
    end,
  },

  { 'bfrg/vim-cpp-modern' },

  -- Rust
  { 'rust-lang/rust.vim' },

  -- Latex
  {
    'lervag/vimtex',
    config = function()
      vim.g.tex_flavor = 'latex'
      vim.g.vimtex_view_method = 'zathura'
      vim.g.vimtex_quickfix_mode = 0
      vim.opt.conceallevel = 0
      vim.g.tex_conceal = 'abdmg'
    end,
  },
  { 'rhysd/vim-grammarous' },

  -- Bazel
  { 'google/vim-maktaba' },
  { 'bazelbuild/vim-bazel', dependencies = { 'google/vim-maktaba' } },

  -- Documentation
  { 'godlygeek/tabular' },
  { 'preservim/vim-markdown', dependencies = { 'godlygeek/tabular' } },
  { 'habamax/vim-rst' },

  -- Protobuf
  { 'uarun/vim-protobuf' },

  -- Beancount
  { 'nathangrigg/vim-beancount' },

  -- Earthly
  { 'earthly/earthly.vim' },
}
