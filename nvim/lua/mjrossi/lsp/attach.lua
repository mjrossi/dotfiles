-- Buffer-local LSP keymaps, wired once via LspAttach rather than threaded
-- through every server config as an on_attach callback. This is the Nvim 0.11+
-- idiom (:h lsp-attach) and it keeps server specs to just their settings.
--
-- Nvim maps several LSP actions out of the box (K, grn, gra, grr, gri, grt,
-- gO), so those are deliberately not repeated here. What follows are the
-- vim-classic aliases this config has always used.
vim.api.nvim_create_autocmd("LspAttach", {
    group = vim.api.nvim_create_augroup("mjrossi_lsp_attach", { clear = true }),
    callback = function(args)
        local opts = { buffer = args.buf, silent = true }

        -- Python runs pyright and ruff together. Both advertise hover, so
        -- without this K is answered by whichever attached first; pyright's
        -- type information is the useful one.
        local client = vim.lsp.get_client_by_id(args.data.client_id)
        if client and client.name == "ruff" then
            client.server_capabilities.hoverProvider = false
        end

        vim.keymap.set("n", "gd", vim.lsp.buf.definition, opts)
        vim.keymap.set("n", "gr", vim.lsp.buf.references, opts)
        vim.keymap.set("n", "gD", vim.lsp.buf.declaration, opts)
        vim.keymap.set("n", "gi", vim.lsp.buf.implementation, opts)
        vim.keymap.set("n", "gt", vim.lsp.buf.type_definition, opts)
        vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, opts)
        vim.keymap.set({ "n", "v" }, "<leader>ca", vim.lsp.buf.code_action, opts)
        vim.keymap.set("n", "<leader>rs", "<cmd>lsp restart<cr>", opts)

        vim.keymap.set("n", "gl", vim.diagnostic.open_float, opts)
        vim.keymap.set("n", "[d", function() vim.diagnostic.jump({ count = -1 }) end, opts)
        vim.keymap.set("n", "]d", function() vim.diagnostic.jump({ count = 1 }) end, opts)
        vim.keymap.set("n", "<leader>q", vim.diagnostic.setloclist, opts)
    end,
})
