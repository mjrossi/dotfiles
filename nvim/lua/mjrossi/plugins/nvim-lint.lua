return {
    "mfussenegger/nvim-lint",
    event = { "BufReadPre", "BufNewFile" },
    config = function()
        local lint = require("lint")

        -- No python entry: the ruff language server publishes those
        -- diagnostics itself, so linting here would duplicate them.
        lint.linters_by_ft = {
            ruby = { "rubocop" },
            go = { "golangcilint" },
        }

        vim.api.nvim_create_autocmd({ "BufWritePost", "BufReadPost", "InsertLeave" }, {
            callback = function()
                lint.try_lint()
            end,
        })
    end,
}
