return {
    "ejrichards/mise.nvim",
    opts = {
        -- Re-run mise env when changing directories inside Neovim so LSP servers
        -- and tools pick up the correct versions for the new project.
        mise_command = "mise",
    },
}
