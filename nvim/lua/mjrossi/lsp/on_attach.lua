-- Shared on_attach used by every LSP server: wires standard LSP + diagnostic
-- keymaps. Kept in one place so lsp-zero.lua and ruby-lsp.lua stay in sync.
return function(client, bufnr)
    local opts = { buffer = bufnr, silent = true }

    vim.keymap.set("n", "gd", vim.lsp.buf.definition, opts)
    vim.keymap.set("n", "gr", vim.lsp.buf.references, opts)
    vim.keymap.set("n", "gD", vim.lsp.buf.declaration, opts)
    vim.keymap.set("n", "gi", vim.lsp.buf.implementation, opts)
    vim.keymap.set("n", "gt", vim.lsp.buf.type_definition, opts)
    vim.keymap.set("n", "K", vim.lsp.buf.hover, opts)
    vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, opts)
    vim.keymap.set({ "n", "v" }, "<leader>ca", vim.lsp.buf.code_action, opts)
    vim.keymap.set("n", "<leader>rs", ":LspRestart<CR>", opts)

    vim.keymap.set("n", "gl", vim.diagnostic.open_float, opts)
    vim.keymap.set("n", "[d", function() vim.diagnostic.jump({ count = -1 }) end, opts)
    vim.keymap.set("n", "]d", function() vim.diagnostic.jump({ count = 1 }) end, opts)
    vim.keymap.set("n", "<leader>q", vim.diagnostic.setloclist, opts)
end
