return {
    "R-nvim/R.nvim",
    -- Load at startup: R.nvim registers its own FileType handlers and only
    -- does real work in R buffers. Upstream's README needs this only when
    -- defaults.lazy = true; it is explicit here so that never bites.
    lazy = false,
    config = function()
        require("r").setup({
            R_args = { "--quiet", "--no-save" },
            -- Almost all of R.nvim's ~80 defaults live under <localleader>, which
            -- is also <leader> here, so they would shadow <leader>rn (rename),
            -- <leader>rs (LSP restart), <leader>aa (Claude accept diff) and
            -- friends in R buffers. Opt out of all of them and bind the
            -- handful that matter below.
            --
            -- Completion, hover, go-to-definition and rename come from R.nvim's
            -- own language server (r_ls), which attaches to R buffers by itself.
            -- r_language_server is deliberately not enabled alongside it: two
            -- servers mean duplicate completions and hovers, and it needs the
            -- `languageserver` package in every project library. Formatting is
            -- air via conform, independent of either.
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
                    -- RStudio's Alt+-; needs macos-option-as-alt in ghostty/config.
                    map("i", "<M-->", "RInsertAssign", "Insert <-")
                end,
            },
        })
    end,
}
