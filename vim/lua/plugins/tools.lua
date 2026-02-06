return {
  -- AI completion
  {
    'supermaven-inc/supermaven-nvim',
    event = 'InsertEnter',
    opts = {},
  },

  -- Claude Code integration
  {
    'coder/claudecode.nvim',
    dependencies = { 'folke/snacks.nvim' },
    event = 'VeryLazy',
    opts = {
      terminal_cmd = 'ccc --allow-all',
      focus_after_send = true,
    },
    keys = {
      { '<leader>ac', '<cmd>ClaudeCodeToggle<cr>', desc = 'Toggle Claude Code' },
      { '<leader>af', '<cmd>ClaudeCodeFocus<cr>', desc = 'Focus Claude Code' },
      { '<leader>as', '<cmd>ClaudeCodeSend<cr>', mode = { 'n', 'v' }, desc = 'Send to Claude Code' },
      { '<leader>aa', '<cmd>ClaudeCodeDiffAccept<cr>', desc = 'Accept diff' },
      { '<leader>ad', '<cmd>ClaudeCodeDiffReject<cr>', desc = 'Reject diff' },
    },
  },
}
