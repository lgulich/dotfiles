-- General options

-- Set python path for neovim
if vim.fn.has('mac') == 1 then
  vim.g.python3_host_prog = '/usr/local/bin/python3'
else
  vim.g.python3_host_prog = '/usr/bin/python3'
end

local opt = vim.opt

-- General
opt.compatible = false
opt.autoread = true
opt.swapfile = false

-- Indentation and text width
opt.tabstop = 2
opt.shiftwidth = 2
opt.shiftround = true
opt.expandtab = true
opt.autoindent = true
opt.textwidth = 100

-- Searching
opt.incsearch = false

-- Backspace key
opt.backspace = { 'indent', 'eol', 'start' }

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
opt.showcmd = true
opt.colorcolumn = '+1'
opt.ruler = true
opt.scrolloff = 5

-- Enable nice colors in tmux
if vim.env.TMUX == nil or vim.env.TMUX == '' then
  if vim.fn.has('termguicolors') == 1 then
    opt.termguicolors = true
  end
end

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
