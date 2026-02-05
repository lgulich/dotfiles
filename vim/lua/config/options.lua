-- General options

local opt = vim.opt

-- General
opt.autoread = true
opt.swapfile = false

-- Indentation and text width
opt.tabstop = 2
opt.shiftwidth = 2
opt.shiftround = true
opt.expandtab = true
opt.textwidth = 100

-- Searching
opt.incsearch = false

-- Navigation
opt.iskeyword:append('_')

-- Folding
opt.foldenable = true
opt.foldlevelstart = 10
opt.foldnestmax = 1
opt.foldmethod = 'indent'

-- Line numbering
opt.number = true
opt.relativenumber = true

-- Spellcheck
opt.spell = true
opt.spelllang = 'en'
opt.spellfile = vim.fn.expand('$DOTFILES') .. '/vim/spell/en.utf-8.add'

-- Appearance
opt.showmatch = true
opt.colorcolumn = '+1'
opt.scrolloff = 5
opt.termguicolors = true
opt.signcolumn = 'yes'

-- Setup make for bazel and gcc
opt.makeprg = 'bazel build'
opt.errorformat:prepend('%*[^:]: %f:%l:%*[^:]:%m')
opt.errorformat:append('%+GIn file included from %f:%l%*[,:]')

-- Autocommands
local augroup = vim.api.nvim_create_augroup('Options', { clear = true })

-- Disable auto-line-wrapping for shell scripts and javascript
vim.api.nvim_create_autocmd('FileType', {
  group = augroup,
  pattern = { 'sh', 'bash', 'zsh', 'js' },
  callback = function()
    vim.bo.textwidth = 0
  end,
})

-- Enable spellcheck for tex files
vim.api.nvim_create_autocmd('FileType', {
  group = augroup,
  pattern = { 'tex', 'latex' },
  callback = function()
    vim.bo.spell = true
  end,
})

-- Set C/C++ comment style to //
vim.api.nvim_create_autocmd('FileType', {
  group = augroup,
  pattern = { 'c', 'cpp' },
  callback = function()
    vim.bo.commentstring = '// %s'
  end,
})

-- Highlight on yank
vim.api.nvim_create_autocmd('TextYankPost', {
  group = augroup,
  callback = function()
    vim.highlight.on_yank()
  end,
})

-- Change caret shape to I-beam in insert mode
vim.api.nvim_create_autocmd('InsertEnter', {
  group = augroup,
  pattern = '*',
  callback = function()
    vim.opt.cursorline = true
  end,
})

vim.api.nvim_create_autocmd('InsertLeave', {
  group = augroup,
  pattern = '*',
  callback = function()
    vim.opt.cursorline = false
  end,
})
