-- Disable the legacy remote-plugin hosts. Nothing in the plugin list uses one,
-- so leaving them on only asks :checkhealth to report four missing packages
-- for a mechanism this config never touches.
vim.g.loaded_node_provider = 0
vim.g.loaded_perl_provider = 0
vim.g.loaded_python3_provider = 0
vim.g.loaded_ruby_provider = 0

-- Neovim ships no mdx filetype, and nothing in the plugin set adds one, so .mdx
-- blog posts open with an empty filetype: mdx_analyzer can never attach and
-- there is no highlighting. Name the filetype, then point treesitter at the
-- markdown parser (already installed) since there is no mdx grammar.
vim.filetype.add({ extension = { mdx = "mdx" } })
vim.treesitter.language.register("markdown", "mdx")

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
