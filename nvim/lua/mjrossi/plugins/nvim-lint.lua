return {
    "mfussenegger/nvim-lint",
    ft = { "go", "ruby" },
    config = function()
        local lint = require("lint")

        -- No python entry: the ruff language server publishes those
        -- diagnostics itself, so linting here would duplicate them.
        lint.linters_by_ft = {
            ruby = { "rubocop" },
            go = { "golangcilint" },
        }

        local group = vim.api.nvim_create_augroup("mjrossi-lint", { clear = true })
        vim.api.nvim_create_autocmd("BufWritePost", {
            group = group,
            callback = function()
                lint.try_lint()
            end,
        })
        vim.api.nvim_create_autocmd("FileType", {
            group = group,
            pattern = { "go", "ruby" },
            callback = function()
                lint.try_lint()
            end,
        })

        -- The FileType event that loaded this plugin has already fired, so
        -- schedule the initial pass for the current buffer explicitly.
        vim.schedule(lint.try_lint)
    end,
}
