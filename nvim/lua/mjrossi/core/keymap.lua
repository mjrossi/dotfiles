vim.g.mapleader = '\\'

vim.keymap.set("n", "<left>", vim.cmd.tabp, { desc = "Previous Tab" })
vim.keymap.set("n", "<right>", vim.cmd.tabn, { desc = "Next Tab" })

vim.keymap.set("n", "<leader>nh", ':noh<CR>', {
    desc = "Turns off highlighting from last search",
    silent = true,
})
