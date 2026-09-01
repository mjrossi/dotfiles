return {
    "nvim-tree/nvim-tree.lua",
    version = "*",
    cmd = { "NvimTreeFindFile", "NvimTreeToggle" },
    keys = {
        { "<leader>nt", "<cmd>NvimTreeToggle<cr>", desc = "Open nvim-tree" },
        { "<leader>nf", "<cmd>NvimTreeFindFile<cr>", desc = "Open nvim-tree to file" },
    },
    dependencies = {
        "nvim-tree/nvim-web-devicons",
    },
    opts = {},
}
