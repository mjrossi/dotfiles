-- snacks was already being pulled in as a claudecode.nvim dependency and loaded
-- eagerly at priority 1000 with no modules enabled. It owns its own spec now,
-- and its picker replaces telescope (plus telescope-fzf-native and plenary).
--
-- The picker shells out to fd and ripgrep, both already installed via mise, so
-- there is no native build step to keep working.
return {
    "folke/snacks.nvim",
    priority = 1000,
    lazy = false,
    opts = {
        picker = {
            enabled = true,
            -- Carried over from telescope's file_ignore_patterns. These are
            -- passed through as `fd -E <glob>` and `rg -g '!<glob>'`, so they
            -- are bare directory names rather than Lua patterns.
            --
            -- Top level rather than per-source: snacks merges defaults ->
            -- these -> sources[name] -> call opts, and one source never
            -- inherits from another. grep_word is its own source, so listing
            -- `grep` under `sources` would have left <leader>fw searching
            -- vendor/ and node_modules/ -- which is what telescope's
            -- `defaults` block covered.
            exclude = { "vendor", "node_modules", ".git" },
        },
    },
    keys = {
        { "<leader>ff", function() Snacks.picker.files() end,     desc = "Find Files" },
        { "<leader>fg", function() Snacks.picker.grep() end,      desc = "Live Grep" },
        { "<leader>fb", function() Snacks.picker.buffers() end,   desc = "Find Buffer" },
        { "<leader>fh", function() Snacks.picker.help() end,      desc = "Find Help" },
        { "<leader>fw", function() Snacks.picker.grep_word() end, desc = "Find word under cursor" },
    },
}
