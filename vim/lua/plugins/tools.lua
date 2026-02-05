return {
  -- Remote development
  {
    'nosduco/remote-sshfs.nvim',
    dependencies = { 'nvim-lua/plenary.nvim', 'nvim-telescope/telescope.nvim' },
    config = function()
      require('remote-sshfs').setup({
        connections = {
          sshfs_args = {
            "-o reconnect",
            "-o ConnectTimeout=5",
            "-o cache=yes",
            "-o kernel_cache",
            "-o auto_cache",
          },
        },
      })
      require('telescope').load_extension 'remote-sshfs'
    end,
  },

  -- AI
  { 'supermaven-inc/supermaven-nvim', config = function() require('supermaven-nvim').setup{} end },
}
