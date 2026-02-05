-- Custom commands and functions

-- Remove trailing whitespaces
local function trim_whitespace()
  local save = vim.fn.winsaveview()
  vim.cmd([[keeppatterns %s/\s\+$//e]])
  vim.fn.winrestview(save)
end

vim.api.nvim_create_user_command('TrimWhiteSpace', trim_whitespace, {})

-- Create tags in current directory
vim.api.nvim_create_user_command('MakeTags', '!ctags -R .', {})

-- Insert a 128-bit uuid
vim.api.nvim_create_user_command('InsertUuid', function()
  local uuid = vim.fn.system("printf '0x%s\\n' $(uuidgen -r | tr -d '-' | cut -b 1-16)")
  vim.api.nvim_put({ uuid:gsub('\n', '') }, 'l', true, true)
end, {})

-- Write with sudo even when vim was not opened with sudo
vim.api.nvim_create_user_command('WriteWithSudo', 'w !sudo tee %', {})

-- Get the remote URL to the current line
vim.api.nvim_create_user_command('GetRemoteUrl', function()
  local git_url = vim.fn.system('git config --get remote.origin.url'):gsub('\n$', '')
  git_url = git_url:gsub('(.*)@(.*):(%d*/)?(.*)%.git', 'https://%2/%4')
  local branch = vim.fn.system('git rev-parse --abbrev-ref HEAD'):gsub('\n$', '')
  local file = vim.fn.system('git ls-files --full-name ' .. vim.fn.expand('%')):gsub('\n$', '')
  local line = vim.fn.line('.')
  local url = git_url .. '/blob/' .. branch .. '/' .. file .. '#L' .. line
  vim.fn.setreg('+', url)
  print(url)
end, {})

-- Autocommands
local augroup = vim.api.nvim_create_augroup('CustomCommands', { clear = true })

-- Automatically remove white space on file save
vim.api.nvim_create_autocmd('BufWritePre', {
  group = augroup,
  pattern = '*',
  callback = trim_whitespace,
})

-- Set jenkinsfile filetype to groovy
vim.api.nvim_create_autocmd({ 'BufNewFile', 'BufRead' }, {
  group = augroup,
  pattern = '*.jenkinsfile',
  callback = function()
    vim.bo.filetype = 'groovy'
  end,
})
