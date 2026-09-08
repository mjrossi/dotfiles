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
                    workspace = { checkThirdParty = false },
                },
            },
        }

        -- Volar-based servers -- Vue, Svelte, Astro, mdx_analyzer -- embed
        -- TypeScript's JavaScript Language Service API, and TypeScript 7 (the
        -- Go port) no longer exposes it. Upstream's guidance is that projects
        -- using these tools stay on TypeScript 6 until TS ships a replacement
        -- API; Astro itself still devDepends on typescript 6.
        --
        -- lspconfig points mdx_analyzer at the first node_modules/typescript/lib
        -- found walking up from the project root, sight unseen. Under TypeScript
        -- 7 that directory holds native binaries and a tsc.js shim -- no
        -- typescript.js and no tsserverlibrary.js -- so Volar's loadTsdkByPath
        -- throws during initialize and every .mdx buffer opens on an RPC stack
        -- trace. Check the lib first and say what is actually wrong instead.
        local function usable_tsdk(root_dir)
            local lib = require("lspconfig.util").get_typescript_server_path(root_dir)
            if not lib or lib == "" then
                return false
            end
            -- Volar takes either entrypoint. TS 6 ships both, TS 7 ships neither.
            for _, entrypoint in ipairs({ "typescript.js", "tsserverlibrary.js" }) do
                if vim.uv.fs_stat(lib .. "/" .. entrypoint) then
                    return true
                end
            end
            return false
        end

        local warned_roots = {}

        vim.lsp.config.mdx_analyzer = {
            -- root_markers is ignored once root_dir is a function (:h
            -- lsp-root_dir()), so package.json moves here. Returning without
            -- calling on_dir is the documented way to leave a server unstarted.
            root_dir = function(bufnr, on_dir)
                local root = vim.fs.root(bufnr, "package.json")
                if not root then
                    return
                end
                if usable_tsdk(root) then
                    on_dir(root)
                elseif not warned_roots[root] then
                    warned_roots[root] = true
                    vim.notify(
                        "mdx_analyzer not started: no TypeScript with a JavaScript API in "
                            .. root .. " -- Volar needs typescript 6 or older",
                        vim.log.levels.WARN
                    )
                end
            end,
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
        vim.lsp.enable("mdx_analyzer")
        vim.lsp.enable("pyright")
        vim.lsp.enable("ruff")
        vim.lsp.enable("yamlls")
    end,
}
