return {
    "nvim-treesitter/nvim-treesitter",
    version = "*",
    lazy = false,
    build = ":TSUpdate",
    config = function()
        local configs = require("nvim-treesitter.configs")

        configs.setup({
            ensure_installed = { "c", "lua", "vim", "vimdoc", "query", "elixir", "heex", "javascript", "html", "go",
                "gomod", "gosum", "ruby", "python" },
            sync_install = false,
            highlight = { enable = true },
            indent = { enable = true },
        })
    end
}
