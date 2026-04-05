return {
    "neovim/nvim-lspconfig",
    event = { "BufReadPre", "BufNewFile" },
    dependencies = {
        "hrsh7th/cmp-nvim-lsp",
    },
    config = function()
        local cmp_nvim_lsp = require("cmp_nvim_lsp")

        -- Default capabilities with completion support
        local capabilities = cmp_nvim_lsp.default_capabilities()

        -- Default on_attach function for keymaps
        local on_attach = function(client, bufnr)
            local opts = { buffer = bufnr, silent = true }

            -- Set keybindings
            vim.keymap.set("n", "gd", vim.lsp.buf.definition, opts)
            vim.keymap.set("n", "gr", vim.lsp.buf.references, opts)
            vim.keymap.set("n", "gD", vim.lsp.buf.declaration, opts)
            vim.keymap.set("n", "gi", vim.lsp.buf.implementation, opts)
            vim.keymap.set("n", "gt", vim.lsp.buf.type_definition, opts)
            vim.keymap.set("n", "K", vim.lsp.buf.hover, opts)
            vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, opts)
            vim.keymap.set({ "n", "v" }, "<leader>ca", vim.lsp.buf.code_action, opts)
            vim.keymap.set("n", "<leader>rs", ":LspRestart<CR>", opts)

            -- Diagnostic keybindings
            vim.keymap.set("n", "gl", vim.diagnostic.open_float, opts)
            vim.keymap.set("n", "[d", function() vim.diagnostic.jump({ count = -1 }) end, opts)
            vim.keymap.set("n", "]d", function() vim.diagnostic.jump({ count = 1 }) end, opts)
            vim.keymap.set("n", "<leader>q", vim.diagnostic.setloclist, opts)
        end

        -- Apply shared capabilities and on_attach to all servers
        -- Individual server configs below will merge/override as needed
        vim.lsp.config('*', {
            capabilities = capabilities,
            on_attach = on_attach,
        })

        -- Configure gopls using new nvim 0.11 API
        vim.lsp.config.gopls = {
            cmd = { "gopls" },
            filetypes = { "go", "gomod", "gowork", "gotmpl" },
            root_markers = { "go.work", "go.mod", ".git" },
            capabilities = capabilities,
            on_attach = on_attach,
            settings = {
                gopls = {
                    analyses = {
                        unusedparams = true,
                    },
                    buildFlags = { '-tags=demo,testdb' },
                    staticcheck = true,
                },
            },
        }

        -- Configure lua_ls using new nvim 0.11 API
        vim.lsp.config.lua_ls = {
            cmd = { "lua-language-server" },
            filetypes = { "lua" },
            root_markers = { ".luarc.json", ".luarc.jsonc", ".luacheckrc", ".stylua.toml", "stylua.toml", "selene.toml", "selene.yml", ".git" },
            capabilities = capabilities,
            on_attach = on_attach,
            settings = {
                Lua = {
                    runtime = {
                        version = "LuaJIT",
                    },
                    diagnostics = {
                        globals = { "vim" },
                    },
                    workspace = {
                        library = vim.api.nvim_get_runtime_file("", true),
                        checkThirdParty = false,
                    },
                },
            },
        }

        -- Configure yamlls using new nvim 0.11 API
        vim.lsp.config.yamlls = {
            cmd = { "yaml-language-server", "--stdio" },
            filetypes = { "yaml", "yaml.docker-compose", "yaml.gitlab" },
            root_markers = { ".git" },
            capabilities = capabilities,
            on_attach = on_attach,
            settings = {
                yaml = {
                    schemas = {
                        ["https://json.schemastore.org/github-workflow.json"] = "/.github/workflows/*",
                        ["https://json.schemastore.org/dependabot-2.0.json"] = "*/dependabot.yml",
                    },
                },
            },
        }

        -- Configure pyright to use the mise-managed Python shim.
        -- The shim resolves to the correct Python version based on the project's .mise.toml.
        vim.lsp.config.pyright = {
            cmd = { "pyright-langserver", "--stdio" },
            filetypes = { "python" },
            root_markers = { "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "pyrightconfig.json", ".git" },
            capabilities = capabilities,
            on_attach = on_attach,
            settings = {
                python = {
                    pythonPath = vim.fn.expand("~/.local/share/mise/shims/python"),
                },
            },
        }

        -- Enable the configured servers
        vim.lsp.enable("gopls")
        vim.lsp.enable("lua_ls")
        vim.lsp.enable("pyright")
        vim.lsp.enable("yamlls")
    end,
}
