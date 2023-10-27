return {
    "VonHeikemen/lsp-zero.nvim",
    branch = "v3.x",
    lazy = true,
    config = function()
        local lsp = require("lsp-zero")
        local neodev = require("neodev")
        local config = require('lspconfig')

        lsp.preset('recommended')

        lsp.on_attach(function(_, bufnr)
            lsp.default_keymaps({ buffer = bufnr })
        end)

        lsp.format_on_save({
            servers = {
                ['lua_ls'] = { 'lua' },
                ['rust_analyzer'] = { 'rust' },
                ['gopls'] = { 'go' },
            }
        })

        neodev.setup({})

        config.gopls.setup({
            settings = {
                analysis = {
                    unusedparams = true,
                },
                gopls = {
                    buildFlags = { '-tags', 'demo,testdb' },
                },
                staticcheck = true,
            }
        })


        config.lua_ls.setup({
            settings = {
                Lua = {
                    runtime = {
                        version = "LuaJIT",
                    },
                },
            },
        })

        config.yamlls.setup({
            settings = {
                yaml = {
                    schemas = {
                        ["https://json.schemastore.org/github-workflow.json"] = "/.github/workflows/*",
                        ["https://json.schemastore.org/dependabot-2.0.json"] = "*/dependabot.yml",
                    }
                }
            }
        })
    end,
    dependencies = {
        "neovim/nvim-lspconfig",
        "hrsh7th/nvim-cmp",
    },
}
