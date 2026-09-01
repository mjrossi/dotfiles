return {
    "ejrichards/mise.nvim",
    cmd = "Mise",
    event = "DirChanged",
    -- Re-run mise env when changing directories inside Neovim so LSP servers
    -- and tools pick up the correct versions for the new project. The plugin's
    -- default `run = "mise"` is the desired command.
    opts = {},
}
