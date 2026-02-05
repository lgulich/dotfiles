return {
  {
    'joshdick/onedark.vim',
    priority = 1000,
    config = function()
      pcall(vim.cmd, 'colorscheme onedark')
    end,
  },
}
