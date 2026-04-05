return {
    "williamboman/mason.nvim",
    dependencies = {
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
                "elixirls",
                "gopls",
                "lua_ls",
                "pyright",
                "rust_analyzer",
                "taplo",
                "yamlls",
            },
            -- Automatically enable installed servers.
            -- Servers explicitly configured in lsp-zero.lua (using vim.lsp.config) will use those configs.
            automatic_enable = true,
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
