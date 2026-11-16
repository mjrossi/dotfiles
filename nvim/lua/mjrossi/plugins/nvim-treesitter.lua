return {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    lazy = false,
    build = ":TSUpdate",
    config = function()
        -- Grouped by purpose rather than one per line, so stylua leaves it be.
        -- stylua: ignore
        require("nvim-treesitter").install({
            "c", "lua", "vim", "vimdoc", "query", "markdown", "markdown_inline",
            "elixir", "heex", "javascript", "html", "go",
            "gomod", "gosum", "ruby", "python", "just",
            "r", "rnoweb", "yaml", "csv", -- R.nvim: .R, .Rnw, .Rmd front matter, data.frame viewer
            -- What this dotfiles repo itself is made of, plus git's own buffers.
            "fish", "toml", "kdl", "bash", "json",
            "diff", "gitcommit", "git_config", "ssh_config",
        })

        -- A named, cleared group so re-sourcing this spec replaces the
        -- autocmd instead of stacking a second copy.
        vim.api.nvim_create_autocmd("FileType", {
            group = vim.api.nvim_create_augroup("mjrossi-treesitter", { clear = true }),
            callback = function()
                if pcall(vim.treesitter.start) then
                    vim.bo.indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
                end
            end,
        })
    end,
}
