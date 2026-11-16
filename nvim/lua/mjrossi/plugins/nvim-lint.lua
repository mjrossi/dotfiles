return {
    "mfussenegger/nvim-lint",
    ft = { "go" },
    config = function()
        local lint = require("lint")

        -- No python or ruby entry: the ruff and ruby-lsp language servers
        -- publish those diagnostics themselves (ruby-lsp via the project's
        -- bundled rubocop), so linting here would duplicate them.
        lint.linters_by_ft = {
            go = { "golangcilint" },
        }

        local group = vim.api.nvim_create_augroup("mjrossi-lint", { clear = true })
        vim.api.nvim_create_autocmd("BufWritePost", {
            group = group,
            callback = function() lint.try_lint() end,
        })
        vim.api.nvim_create_autocmd("FileType", {
            group = group,
            pattern = { "go" },
            callback = function() lint.try_lint() end,
        })

        -- The FileType event that loaded this plugin has already fired, so
        -- schedule the initial pass for the current buffer explicitly.
        vim.schedule(lint.try_lint)
    end,
}
