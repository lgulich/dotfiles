return {
  { '907th/vim-auto-save', config = function() vim.g.auto_save = 1 end },

  {
    'chiel92/vim-autoformat',
    config = function()
      vim.keymap.set('', '<F3>', ':Autoformat<CR>')
    end,
  },

  { 'junegunn/fzf', dir = '~/.fzf', build = './install --all' },

  {
    'junegunn/fzf.vim',
    config = function()
      vim.keymap.set('', '<C-p>', ':Files<CR>')
    end,
  },

  {
    'scrooloose/nerdtree',
    config = function()
      vim.keymap.set('', '<C-n>', ':NERDTreeToggle<CR>')
      vim.keymap.set('', '<leader>f', ':NERDTreeFind<CR>')

      -- NERDTree preview functionality
      vim.g.nerd_preview_enabled = 0
      vim.g.preview_last_buffer = 0

      vim.cmd([[
        function! NERDTreePreview()
          if (&ft ==# 'nerdtree')
            let l:filename = substitute(getline("."), "^\s\+\|\s\+$","","g")
            let l:lastchar = strpart(l:filename, strlen(l:filename) - 1, 1)
            if (l:lastchar != "/" && strpart(l:filename, 0 ,2) != "..")
              let l:store_buffer_to_close = 1
              if (bufnr(l:filename) > 0)
                let l:store_buffer_to_close = 0
              endif
              execute "normal go"
              if (g:preview_last_buffer > 0)
                execute "bwipeout " . g:preview_last_buffer
                let g:preview_last_buffer = 0
              endif
              if (l:store_buffer_to_close)
                let g:preview_last_buffer = bufnr(l:filename)
              endif
            endif
          elseif (g:preview_last_buffer > 0)
            let g:preview_last_buffer = 0
          endif
        endfunction

        function! NERDTreePreviewToggle()
          if (g:nerd_preview_enabled)
            let g:nerd_preview_enabled = 0
            augroup nerdpreview
              autocmd!
            augroup END
          else
            let g:nerd_preview_enabled = 1
            augroup nerdpreview
              autocmd!
              autocmd CursorMoved * nested call NERDTreePreview()
            augroup END
          endif
        endfunction
      ]])
    end,
  },

  {
    'tpope/vim-commentary',
    config = function()
      vim.api.nvim_create_autocmd('FileType', {
        pattern = { 'c', 'cpp' },
        callback = function()
          vim.bo.commentstring = '// %s'
        end,
      })
    end,
  },

  {
    'tpope/vim-fugitive',
    config = function()
      vim.keymap.set('n', '<leader>gd', ':Gvdiff<CR>')
      vim.keymap.set('n', 'dgh', ':diffget //2<CR>')
      vim.keymap.set('n', 'dgl', ':diffget //3<CR>')
    end,
  },

  { 'tpope/vim-surround' },
  { 'tpope/vim-repeat' },
  { 'tpope/vim-abolish' },
  { 'vim-airline/vim-airline' },

  {
    'bkad/CamelCaseMotion',
    config = function()
      vim.keymap.set('', 'w', '<Plug>CamelCaseMotion_w', { silent = true })
      vim.keymap.set('', 'b', '<Plug>CamelCaseMotion_b', { silent = true })
      vim.keymap.set('', 'e', '<Plug>CamelCaseMotion_e', { silent = true })
      vim.keymap.set('', 'ge', '<Plug>CamelCaseMotion_ge', { silent = true })
      vim.cmd('sunmap w')
      vim.cmd('sunmap b')
      vim.cmd('sunmap e')
      vim.cmd('sunmap ge')
    end,
  },

  { 'APZelos/blamer.nvim', config = function() vim.g.blamer_enabled = 1 end },
  { 'ActivityWatch/aw-watcher-vim' },
}
