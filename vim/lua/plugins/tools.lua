return {
  -- Remote development
  {
    'nosduco/remote-sshfs.nvim',
    dependencies = { 'nvim-lua/plenary.nvim', 'nvim-telescope/telescope.nvim' },
    cmd = { 'RemoteSSHFSConnect', 'RemoteSSHFSDisconnect', 'RemoteSSHFSEdit', 'RemoteSSHFSFindFiles', 'RemoteSSHFSLiveGrep' },
    opts = {
      connections = {
        sshfs_args = {
          '-o reconnect',
          '-o ConnectTimeout=5',
          '-o cache=yes',
          '-o kernel_cache',
          '-o auto_cache',
        },
      },
    },
    config = function(_, opts)
      require('remote-sshfs').setup(opts)
      require('telescope').load_extension('remote-sshfs')
    end,
  },

  -- AI completion
  {
    'supermaven-inc/supermaven-nvim',
    event = 'InsertEnter',
    opts = {},
  },
}
