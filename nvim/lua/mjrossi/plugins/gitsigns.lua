return {
    "lewis6991/gitsigns.nvim",
    event = { "BufReadPre", "BufNewFile" },
    config = function()
        local gitsigns = require("gitsigns")

        gitsigns.setup({
            signs = {
                add = { text = "+" },
                change = { text = "~" },
                delete = { text = "_" },
                topdelete = { text = "‾" },
                changedelete = { text = "~" },
            },
            on_attach = function(bufnr)
                local gs = package.loaded.gitsigns

                local function map(mode, l, r, opts)
                    opts = opts or {}
                    opts.buffer = bufnr
                    vim.keymap.set(mode, l, r, opts)
                end

                -- Navigation. nav_hunk handles diff mode itself, so these need
                -- neither the `vim.wo.diff` guard nor an expr mapping.
                map('n', ']h', function() gs.nav_hunk('next') end, { desc = "Next git hunk" })
                map('n', '[h', function() gs.nav_hunk('prev') end, { desc = "Previous git hunk" })

                -- Actions
                map('n', '<leader>hs', gs.stage_hunk, { desc = "Stage hunk" })
                map('n', '<leader>hr', gs.reset_hunk, { desc = "Reset hunk" })
                map('v', '<leader>hs', function() gs.stage_hunk {vim.fn.line('.'), vim.fn.line('v')} end, { desc = "Stage hunk" })
                map('v', '<leader>hr', function() gs.reset_hunk {vim.fn.line('.'), vim.fn.line('v')} end, { desc = "Reset hunk" })
                map('n', '<leader>hS', gs.stage_buffer, { desc = "Stage buffer" })
                -- stage_hunk toggles, so it also unstages; undo_stage_hunk is retired.
                map('n', '<leader>hu', gs.stage_hunk, { desc = "Unstage hunk (toggle)" })
                map('n', '<leader>hR', gs.reset_buffer, { desc = "Reset buffer" })
                map('n', '<leader>gp', gs.preview_hunk, { desc = "Preview hunk" })
                map('n', '<leader>gb', function() gs.blame_line{full=true} end, { desc = "Blame line" })
                map('n', '<leader>gd', gs.diffthis, { desc = "Diff this" })
                map('n', '<leader>gD', function() gs.diffthis('~') end, { desc = "Diff this ~" })
            end,
        })
    end,
}
