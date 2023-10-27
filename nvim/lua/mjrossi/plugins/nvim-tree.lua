return {
    "nvim-tree/nvim-tree.lua",
    version = "*",
    lazy = false,
    dependencies = {
        "nvim-tree/nvim-web-devicons",
    },
    config = function()
        require("nvim-tree").setup {}

        vim.keymap.set('n', '<leader>nt', ':NvimTreeToggle<CR>', { desc = "Open nvim-tree" })
        vim.keymap.set('n', '<leader>nf', ':NvimTreeFindFile<CR>', { desc = "Open nvim-tree to file" })
    end,
}
