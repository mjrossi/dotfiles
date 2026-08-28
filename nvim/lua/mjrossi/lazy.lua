local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable", -- latest stable release
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

local plugins = {
  { import = "mjrossi.plugins" },
  { import = "mjrossi.plugins.lsp" },
}

local opts = {
  install = {
    colorscheme = { "tokyonight" },
  },
  checker = {
    enabled = true,
    notify = false,
  },
  change_detection = {
    notify = false,
  },
  -- No plugin here requires luarocks, so skip the hererocks bootstrap entirely
  -- rather than let it fail and report an error on every health check.
  rocks = {
    enabled = false,
  },
}

require("lazy").setup(plugins, opts)
