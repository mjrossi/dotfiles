return {
    "neovim/nvim-lspconfig",
    -- Eager, not BufReadPre: mason-lspconfig's automatic_enable calls
    -- vim.lsp.enable() at startup, which needs lspconfig's lsp/ dir already on
    -- the runtimepath. Lazy-loading it inverted that order, so :checkhealth
    -- reported "config not found" for every server and a buffer created without
    -- a BufReadPre (:enew + :set ft=go) started its server before the
    -- vim.lsp.config('*') defaults below were registered.
    lazy = false,
    dependencies = {
        "saghen/blink.cmp",
    },
    config = function()
        -- Shared capabilities for every server. Keymaps are wired separately
        -- by the LspAttach autocmd in mjrossi.lsp.attach.
        vim.lsp.config('*', {
            capabilities = require("blink.cmp").get_lsp_capabilities(),
        })

        -- Each block below carries only what differs from the definition
        -- nvim-lspconfig ships in its lsp/<name>.lua. Per :h lsp-config, those
        -- files are merged in ahead of anything set here, so repeating cmd,
        -- filetypes or root_markers would only shadow a better upstream value
        -- (gopls resolves its root through GOMODCACHE/GOROOT; yamlls prefers a
        -- project-local node_modules binary; both are functions we cannot
        -- express as a static list).

        vim.lsp.config.gopls = {
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

        vim.lsp.config.lua_ls = {
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

        vim.lsp.config.yamlls = {
            settings = {
                yaml = {
                    schemas = {
                        ["https://json.schemastore.org/github-workflow.json"] = "/.github/workflows/*",
                        ["https://json.schemastore.org/dependabot-2.0.json"] = "*/dependabot.yml",
                    },
                },
            },
        }

        -- Python is split between two servers: pyright does type checking,
        -- ruff does linting and formatting. mjrossi.lsp.attach turns off ruff's
        -- hover so pyright owns K rather than the two answering over each other.
        -- pyright is pointed at the mise-managed Python shim, which resolves to
        -- the correct version for the project's .mise.toml.
        vim.lsp.config.pyright = {
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
        vim.lsp.enable("ruff")
        vim.lsp.enable("yamlls")
    end,
}
