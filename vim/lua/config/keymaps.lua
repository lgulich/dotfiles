-- Key mappings

local map = vim.keymap.set

-- Exit insert mode
map('i', 'jk', '<ESC>')

-- Search and replace word under caret
map('n', '<Leader>s', ':%s/\\<<C-r><C-w>\\>/')
-- Search and replace WORD under caret
map('n', '<Leader>S', ':%s/<C-r><C-W>/')
-- Search and replace visual selection
map('v', '<Leader>s', ':<C-u>%s/<C-r>*/')

-- Start global project-wide search (use telescope live_grep via <leader>fg)

-- Toggle fold around current block
map('n', '<space>', 'za')

-- Move vertically by visual line
map('n', 'j', 'gj')
map('n', 'k', 'gk')

-- Move to beginning / end of line
map('', 'B', '^')
map('', 'E', '$')

-- Copy / Paste from primary (X11) clipboard
map('n', '<Leader>y', '"*y')
map('v', '<Leader>y', '"*y')
map('n', '<Leader>p', '"*p')

-- Copy / Paste from clipboard (ctrl-c) clipboard
map('n', '<Leader>Y', '"+y')
map('v', '<Leader>Y', '"+y')
map('n', '<Leader>P', '"+p')

-- Autocorrect the last spell error
map('i', '<C-l>', '<c-g>u<Esc>[s1z=`]a<c-g>u')
map('n', '<C-l>', '1z=1<CR>')

-- Send selection to Claude Code
map('n', '<C-l>', '<cmd>ClaudeCodeFocus<cr>')
map('v', '<C-l>', '<cmd>ClaudeCodeSend<cr>')

-- Toggle terminal
local term_buf = nil
local term_win = nil
local function toggle_terminal()
  if term_win and vim.api.nvim_win_is_valid(term_win) then
    vim.api.nvim_win_hide(term_win)
    term_win = nil
  else
    vim.cmd('botright split')
    vim.cmd('resize 12')
    if term_buf and vim.api.nvim_buf_is_valid(term_buf) then
      vim.api.nvim_win_set_buf(0, term_buf)
    else
      vim.cmd('terminal')
      term_buf = vim.api.nvim_get_current_buf()
    end
    term_win = vim.api.nvim_get_current_win()
    vim.cmd('startinsert')
  end
end
map({'n', 't'}, '<C-t>', toggle_terminal, {desc = 'Toggle Terminal'})

-- Toggle window zoom
local function toggle_zoom()
  if vim.t.zoomed then
    vim.cmd(vim.t.zoom_winrestcmd)
    vim.t.zoomed = false
  else
    vim.t.zoom_winrestcmd = vim.fn.winrestcmd()
    vim.cmd('resize')
    vim.cmd('vertical resize')
    vim.t.zoomed = true
  end
end
map('n', '<C-z>', toggle_zoom, {desc = 'Toggle window zoom'})

-- Allow moving out of terminal panes easily
map('t', '<C-w>h', [[<C-\><C-n><C-w>h]], {silent = true})
map('t', '<C-w>l', [[<C-\><C-n><C-w>l]], {silent = true})
map('t', '<C-w>j', [[<C-\><C-n><C-w>j]], {silent = true})
map('t', '<C-w>k', [[<C-\><C-n><C-w>k]], {silent = true})

-- Reformat the selection
map('v', '<F4>', ':!clang-format<CR>')
map('n', '<F6>', ':%!pandoc -s --from markdown --to rst<CR>')
