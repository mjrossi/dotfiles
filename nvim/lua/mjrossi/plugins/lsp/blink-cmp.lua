-- Replaces nvim-cmp and its five companion plugins (cmp-nvim-lsp, cmp-buffer,
-- cmp-path, cmp_luasnip, LuaSnip): blink ships LSP, path, buffer and snippet
-- sources in-tree and expands snippets through Nvim's native vim.snippet.
--
-- Pinned to 1.x deliberately. v2 is under active development with breaking
-- changes; there is no reason to ride that in a config that just needs to work.
return {
    "saghen/blink.cmp",
    version = "1.*",
    -- No lazy event: nvim-lspconfig is lazy = false and calls
    -- get_lsp_capabilities() in its config, so blink loads at startup as its
    -- dependency regardless. cmp-nvim-lsp was in exactly this position before.
    opts = {
        -- "none" rather than a preset: these are the nvim-cmp bindings this
        -- config has always used, kept so the muscle memory survives the swap.
        keymap = {
            preset = "none",
            ["<C-space>"] = { "show", "show_documentation", "hide_documentation" },
            ["<C-e>"] = { "hide", "fallback" },
            ["<C-j>"] = { "select_next", "fallback" },
            ["<C-k>"] = { "select_prev", "fallback" },
            ["<C-b>"] = { "scroll_documentation_up", "fallback" },
            ["<C-f>"] = { "scroll_documentation_down", "fallback" },
            -- <CR> accepts only an explicitly selected item (nothing is
            -- preselected below), so Enter still inserts a newline otherwise.
            ["<CR>"] = { "accept", "fallback" },
            -- <C-l> takes the first item without needing to select it first.
            ["<C-l>"] = { "select_and_accept", "fallback" },
            -- Snippet placeholder navigation. The old nvim-cmp setup loaded
            -- LuaSnip but never mapped a jump key, so expanding a multi-slot
            -- snippet left you stranded. "fallback" keeps Tab ordinary
            -- everywhere else.
            ["<Tab>"] = { "snippet_forward", "fallback" },
            ["<S-Tab>"] = { "snippet_backward", "fallback" },
        },
        completion = {
            list = {
                selection = { preselect = false, auto_insert = false },
            },
            documentation = { auto_show = true },
        },
        sources = {
            default = { "lsp", "path", "snippets", "buffer" },
        },
        signature = { enabled = true },
    },
}
