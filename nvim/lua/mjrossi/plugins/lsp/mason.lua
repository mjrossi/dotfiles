return {
    "williamboman/mason.nvim",
    dependencies = {
        -- lspconfig first: automatic_enable below calls vim.lsp.enable(), which
        -- resolves each server from lspconfig's lsp/ dir on the runtimepath.
        "neovim/nvim-lspconfig",
        "williamboman/mason-lspconfig.nvim",
        "WhoIsSethDaniel/mason-tool-installer.nvim",
    },
    config = function()
        local mason = require("mason")
        local mason_lspconfig = require("mason-lspconfig")
        local mason_tool_installer = require("mason-tool-installer")

        -- enable mason and configure icons
        mason.setup({
            ui = {
                icons = {
                    package_installed = "✓",
                    package_pending = "➜",
                    package_uninstalled = "✗",
                },
            },
        })

        mason_lspconfig.setup({
            -- list of servers for mason to install
            ensure_installed = {
                "gopls",
                "lua_ls",
                "mdx_analyzer", -- .mdx blog posts; see the filetype rule in core/options.lua
                "pyright",
                "taplo",
                "yamlls",
            },
            -- Automatically enable installed servers.
            -- Servers explicitly configured in lsp-zero.lua (using vim.lsp.config) will use those configs.
            -- The exclusions are servers something else already owns. automatic_enable
            -- maps every installed Mason package with an lspconfig entry, which sweeps
            -- up the formatters mason-tool-installer installs below.
            --   ruby_lsp -- ruby-lsp.nvim (plugins/ruby-lsp.lua) owns it, so the gem runs
            --               against the mise-selected Ruby; two owners defeats that.
            --   rubocop  -- conform formats with it and nvim-lint lints with it; the LSP
            --               server publishes the same offenses again, doubling diagnostics.
            --   stylua   -- conform already formats lua with it.
            automatic_enable = { exclude = { "ruby_lsp", "rubocop", "stylua" } },
        })

        mason_tool_installer.setup({
            ensure_installed = {
                "black",           -- python formatter
                "golangci-lint",   -- go linter
                "goimports",       -- go import organizer (used by conform)
                "isort",           -- python import sorter
                "prettier",        -- yaml formatter
                "pylint",          -- python linter
                "rubocop",         -- ruby linter + formatter
                "stylua",          -- lua formatter
                "taplo",           -- toml formatter
            },
        })
    end,
}
