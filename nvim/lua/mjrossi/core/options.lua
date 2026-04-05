-- Prepend mise shims so LSP servers and tools find mise-managed runtimes.
-- Ensures correct versions even when Neovim is launched outside a mise-aware shell.
local mise_shims = vim.fn.expand("~/.local/share/mise/shims")
if vim.fn.isdirectory(mise_shims) == 1 then
    vim.env.PATH = mise_shims .. ":" .. vim.env.PATH
end

vim.opt.number = true
vim.opt.ruler = true
vim.opt.rulerformat = '%25(%n%m%r: %Y [%l,%v] %p%%%)'
vim.opt.shiftwidth = 4
vim.opt.tabstop = 4
vim.opt.expandtab = true
vim.opt.wildmenu = true
vim.opt.termguicolors = true
vim.opt.colorcolumn = "80"
