return {
    "mason-org/mason.nvim",
    dependencies = {
        -- lspconfig first: automatic_enable below calls vim.lsp.enable(), which
        -- resolves each server from lspconfig's lsp/ dir on the runtimepath.
        "neovim/nvim-lspconfig",
        "mason-org/mason-lspconfig.nvim",
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
                "ruff",
                "taplo",
                "yamlls",
            },
            -- Automatically enable installed servers.
            -- Servers explicitly configured in nvim-lspconfig.lua (using vim.lsp.config) will use those configs.
            -- The exclusions are servers something else already owns. automatic_enable
            -- maps every installed Mason package with an lspconfig entry, which sweeps
            -- up the formatters mason-tool-installer installs below.
            --   ruby_lsp -- ruby-lsp.nvim (plugins/ruby-lsp.lua) owns it, so the gem runs
            --               against the mise-selected Ruby; two owners defeats that.
            --   rubocop  -- conform formats with it and nvim-lint lints with it; the LSP
            --               server publishes the same offenses again, doubling diagnostics.
            --   stylua   -- conform already formats lua with it.
            -- ruff is deliberately NOT excluded: unlike rubocop, its server is
            -- the only thing publishing python diagnostics (nvim-lint no longer
            -- has a python entry), so it needs to be enabled. Its formatting
            -- does not clash with conform either, since python is a configured
            -- filetype there and lsp_format only applies as a fallback.
            -- Installing the server also provides the `ruff` binary that
            -- conform's ruff_organize_imports/ruff_format shell out to.
            automatic_enable = { exclude = { "ruby_lsp", "rubocop", "stylua" } },
        })

        mason_tool_installer.setup({
            ensure_installed = {
                "golangci-lint",   -- go linter
                "goimports",       -- go import organizer (used by conform)
                "prettier",        -- yaml formatter
                "rubocop",         -- ruby linter + formatter
                "stylua",          -- lua formatter
                "taplo",           -- toml formatter
            },
        })
    end,
}
