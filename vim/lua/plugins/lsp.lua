return {
  -- Completion
  {
    'hrsh7th/nvim-cmp',
    event = 'InsertEnter',
    dependencies = {
      'hrsh7th/cmp-nvim-lsp',
      'hrsh7th/cmp-buffer',
      'hrsh7th/cmp-path',
      'hrsh7th/cmp-cmdline',
      'L3MON4D3/LuaSnip',
      'saadparwaiz1/cmp_luasnip',
    },
    config = function()
      local cmp = require('cmp')
      local luasnip = require('luasnip')

      cmp.setup({
        snippet = {
          expand = function(args)
            luasnip.lsp_expand(args.body)
          end,
        },
        mapping = cmp.mapping.preset.insert({
          ['<C-b>'] = cmp.mapping.scroll_docs(-4),
          ['<C-f>'] = cmp.mapping.scroll_docs(4),
          ['<C-Space>'] = cmp.mapping.complete(),
          ['<C-e>'] = cmp.mapping.abort(),
          ['<CR>'] = cmp.mapping.confirm({ select = true }),
          ['<Tab>'] = cmp.mapping(function(fallback)
            if cmp.visible() then
              cmp.select_next_item()
            elseif luasnip.expand_or_jumpable() then
              luasnip.expand_or_jump()
            else
              fallback()
            end
          end, { 'i', 's' }),
          ['<S-Tab>'] = cmp.mapping(function(fallback)
            if cmp.visible() then
              cmp.select_prev_item()
            elseif luasnip.jumpable(-1) then
              luasnip.jump(-1)
            else
              fallback()
            end
          end, { 'i', 's' }),
        }),
        sources = cmp.config.sources({
          { name = 'nvim_lsp' },
          { name = 'luasnip' },
          { name = 'path' },
        }, {
          { name = 'buffer' },
        }),
      })

      -- Cmdline completion
      cmp.setup.cmdline(':', {
        mapping = cmp.mapping.preset.cmdline(),
        sources = cmp.config.sources({
          { name = 'path' },
        }, {
          { name = 'cmdline' },
        }),
      })

      -- Search completion
      cmp.setup.cmdline('/', {
        mapping = cmp.mapping.preset.cmdline(),
        sources = {
          { name = 'buffer' },
        },
      })
    end,
  },

  -- LSP keymaps (configured on LspAttach)
  {
    'folke/which-key.nvim',
    event = 'VeryLazy',
    opts = {},
    config = function()
      vim.api.nvim_create_autocmd('LspAttach', {
        callback = function(args)
          local map = function(mode, lhs, rhs, desc)
            vim.keymap.set(mode, lhs, rhs, { buffer = args.buf, desc = desc })
          end
          map('n', 'gd', vim.lsp.buf.definition, 'Go to definition')
          map('n', 'gD', vim.lsp.buf.declaration, 'Go to declaration')
          map('n', 'gi', vim.lsp.buf.implementation, 'Go to implementation')
          map('n', 'K', vim.lsp.buf.hover, 'Hover documentation')
          map('n', '<C-k>', vim.lsp.buf.signature_help, 'Signature help')
          map('n', '<leader>rn', vim.lsp.buf.rename, 'Rename symbol')
          map('n', '<leader>ca', vim.lsp.buf.code_action, 'Code action')
          map('n', '[d', vim.diagnostic.goto_prev, 'Previous diagnostic')
          map('n', ']d', vim.diagnostic.goto_next, 'Next diagnostic')
        end,
      })
    end,
  },
}
