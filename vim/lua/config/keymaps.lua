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

-- Reformat the selection
map('v', '<F4>', ':!clang-format<CR>')
map('n', '<F6>', ':%!pandoc -s --from markdown --to rst<CR>')
