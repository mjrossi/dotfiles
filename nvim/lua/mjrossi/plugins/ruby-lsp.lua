-- ruby-lsp.nvim manages ruby-lsp independently of Mason, ensuring the gem is
-- installed and run against the correct Ruby version as determined by mise.
-- This avoids ABI mismatch issues when switching Ruby versions across projects.
return {
    "adam12/ruby-lsp.nvim",
    dependencies = {
        "neovim/nvim-lspconfig",
        "saghen/blink.cmp",
    },
    ft = { "ruby" },
    config = function()
        local capabilities = require("blink.cmp").get_lsp_capabilities()

        require("ruby-lsp").setup({
            server = {
                capabilities = capabilities,
            },
        })
    end,
}
