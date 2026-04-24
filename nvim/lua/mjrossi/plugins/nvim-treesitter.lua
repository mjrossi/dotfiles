return {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    lazy = false,
    build = ":TSUpdate",
    config = function()
        require("nvim-treesitter").install({
            "c", "lua", "vim", "vimdoc", "query", "markdown", "markdown_inline",
            "elixir", "heex", "javascript", "html", "go",
            "gomod", "gosum", "ruby", "python", "just",
        })

        vim.api.nvim_create_autocmd("FileType", {
            callback = function()
                if pcall(vim.treesitter.start) then
                    vim.bo.indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
                end
            end,
        })
    end
}
