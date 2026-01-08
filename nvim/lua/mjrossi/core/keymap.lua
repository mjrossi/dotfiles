vim.g.mapleader = '\\'

vim.keymap.set("n", "<left>", vim.cmd.tabp, { desc = "Previous Tab" })
vim.keymap.set("n", "<right>", vim.cmd.tabn, { desc = "Next Tab" })

vim.keymap.set("n", "<leader>nh", ':noh<CR>', {
    desc = "Turns off highlighting from last search",
    silent = true,
})

-- Quality-of-Life improvements
vim.keymap.set("n", "Y", "y$", { desc = "Yank to end of line" })
vim.keymap.set("x", "p", '"_dP', { desc = "Paste without yanking" })
vim.keymap.set("x", "*", [[y/\V<C-R>=escape(@",'/\\')<CR><CR>]], { desc = "Search selection" })
