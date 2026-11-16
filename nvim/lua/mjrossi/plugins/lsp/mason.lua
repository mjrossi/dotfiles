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
            -- Append rather than prepend Mason's bin dir to Neovim's PATH, so a
            -- binary from mise or a project pin always wins and Mason's copy is
            -- only the fallback. With the default "prepend", Mason's gopls,
            -- ruff and friends silently shadowed the versions a repo pins.
            PATH = "append",
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
            -- No gopls: mise's install_go_tools task builds it per Go version
            -- (it links against the toolchain), and nvim-lspconfig.lua enables
            -- it explicitly.
            ensure_installed = {
                "lua_ls",
                -- .mdx blog posts; see the filetype rule in core/options.lua
                -- and the TypeScript guard in nvim-lspconfig.lua
                "mdx_analyzer",
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
            --               ruby-lsp also runs the project's bundled rubocop itself,
            --               so it is the single source of Ruby diagnostics and
            --               formatting.
            --   rubocop  -- no longer installed here, but a Mason copy left over from
            --               earlier configs would otherwise be enabled as a second
            --               server and report every offense twice.
            --   stylua   -- conform already formats lua with it.
            -- ruff is deliberately NOT excluded: its server is the only thing
            -- publishing python diagnostics (nvim-lint no longer
            -- has a python entry), so it needs to be enabled. Its formatting
            -- does not clash with conform either, since python is a configured
            -- filetype there and lsp_format only applies as a fallback.
            -- Installing the server also provides the `ruff` binary that
            -- conform's ruff_organize_imports/ruff_format shell out to.
            automatic_enable = { exclude = { "ruby_lsp", "rubocop", "stylua" } },
        })

        mason_tool_installer.setup({
            ensure_installed = {
                -- NOT golangci-lint: mise owns it (per-project pin inside a
                -- repo, global fallback outside), so nvim-lint resolving
                -- `golangcilint` from PATH matches `just lint` and CI. PATH =
                -- "append" above would keep a Mason copy from shadowing it, but
                -- installing one would only add a stale fallback.
                "goimports", -- go import organizer (used by conform)
                "prettier", -- yaml formatter
                "stylua", -- lua formatter
                "taplo", -- toml formatter
            },
        })
    end,
}
