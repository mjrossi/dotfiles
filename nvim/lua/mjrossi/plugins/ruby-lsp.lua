-- ruby-lsp.nvim manages ruby-lsp independently of Mason, ensuring the gem is
-- installed and run against the correct Ruby version as determined by mise.
-- This avoids ABI mismatch issues when switching Ruby versions across projects.
return {
    "adam12/ruby-lsp.nvim",
    dependencies = {
        "neovim/nvim-lspconfig",
    },
    ft = { "ruby" },
    config = function()
        local capabilities = require("cmp_nvim_lsp").default_capabilities()
        local on_attach = require("mjrossi.lsp.on_attach")

        require("ruby-lsp").setup({
            server = {
                capabilities = capabilities,
                on_attach = on_attach,
            },
        })
    end,
}
