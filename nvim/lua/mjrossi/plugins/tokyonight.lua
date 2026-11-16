return {
    "folke/tokyonight.nvim",
    lazy = false,
    priority = 1000,
    -- Night, to match Ghostty (TokyoNight Night) and Zellij (tokyo-night).
    -- The plugin's own default is Moon.
    opts = { style = "night" },
    config = function(_, opts)
        -- A custom config function replaces lazy.nvim's implicit
        -- setup(opts), so opts must be passed on explicitly or it is ignored.
        require("tokyonight").setup(opts)
        vim.cmd([[colorscheme tokyonight]])
    end,
}
