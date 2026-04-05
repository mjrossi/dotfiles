return {
    "stevearc/conform.nvim",
    event = { "BufWritePre" },
    cmd = { "ConformInfo" },
    keys = {
        {
            "<leader>cf",
            function() require("conform").format({ async = true }) end,
            desc = "Format buffer",
        },
    },
    opts = {
        formatters_by_ft = {
            lua = { "stylua" },
            python = { "isort", "black" }, -- isort first for import ordering, then black
            ruby = { "rubocop" },
            go = { "goimports" },          -- goimports includes gofmt; no need for both
            yaml = { "prettier" },
            toml = { "taplo" },
        },
        format_on_save = {
            timeout_ms = 500,
            lsp_fallback = true, -- fall back to LSP formatting for unconfigured filetypes
        },
    },
}
