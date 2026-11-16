vim.g.mapleader = "\\"
vim.g.maplocalleader = "\\"

vim.keymap.set("n", "<left>", vim.cmd.tabp, { desc = "Previous Tab" })
vim.keymap.set("n", "<right>", vim.cmd.tabn, { desc = "Next Tab" })

vim.keymap.set("n", "<leader>nh", ":noh<CR>", {
    desc = "Turns off highlighting from last search",
    silent = true,
})

-- Quality-of-Life improvements. Y (yank to end of line) and visual * (search
-- for the selection) are Nvim defaults, so they are not mapped here.
vim.keymap.set("x", "p", '"_dP', { desc = "Paste without yanking" })
