return {
    "folke/which-key.nvim",
    event = "VeryLazy",
    opts = {
        spec = {
            { "<leader>a", group = "AI / Claude" },
            { "<leader>c", group = "Code" },
            { "<leader>f", group = "Find (Telescope)" },
            { "<leader>g", group = "Git" },
            { "<leader>h", group = "Hunk (Git)" },
            { "<leader>n", group = "Nav / NvimTree" },
            { "<leader>r", group = "Refactor / LSP" },
        },
    },
}
