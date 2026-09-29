return {
    "R-nvim/R.nvim",
    -- Upstream asks not to lazy-load it: it registers its own FileType
    -- handlers and only does real work in r/rmd/quarto buffers.
    lazy = false,
    config = function()
        require("r").setup({
            R_args = { "--quiet", "--no-save" },
            -- R.nvim's ~80 defaults all live under <localleader>, which is
            -- also <leader> here, so they would shadow <leader>rn (rename),
            -- <leader>ca, <leader>a* and friends in R buffers. Opt out of all
            -- of them and bind the handful that matter below. Completion,
            -- hover and diagnostics come from r_language_server, not R.nvim.
            user_maps_only = true,
            hook = {
                on_filetype = function()
                    -- remap: the targets are R.nvim's buffer-local <Plug> maps.
                    local function map(mode, lhs, plug, desc)
                        vim.keymap.set(mode, lhs, "<Plug>" .. plug, { buffer = true, remap = true, desc = desc })
                    end
                    -- RStudio's Cmd+Enter: run the line and step down, or the selection.
                    map("n", "<CR>", "RDSendLine", "R: send line")
                    map("v", "<CR>", "RSendSelection", "R: send selection")
                    map("n", "<leader>xs", "RStart", "Start R")
                    map("n", "<leader>xq", "RClose", "Quit R")
                    map("n", "<leader>xc", "RDSendChunk", "Send chunk")
                    map("n", "<leader>xa", "RSendFile", "Send file")
                    map("n", "<leader>xh", "RHelp", "Help for word")
                    map("n", "<leader>xv", "RViewDF", "View data.frame")
                end,
            },
        })
    end,
}
