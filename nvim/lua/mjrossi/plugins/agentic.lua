-- Copilot CLI in the editor, over ACP (Agent Client Protocol).
--
-- Copilot is the one agent here with FIRST-PARTY ACP support: the provider
-- below spawns `copilot --acp --stdio` directly, with no bridge process in
-- between. Claude Code and Codex would each need a third-party npm bridge
-- (@agentclientprotocol/claude-agent-acp, .../codex-acp) because neither CLI
-- speaks ACP natively -- `claude` only offers its own --ide websocket
-- protocol, which claudecode.nvim already implements. So Claude stays on
-- claudecode.nvim and only Copilot is configured here. Adding a bridged
-- provider later is an entry in `acp_providers`, not a new plugin.
--
-- `copilot` comes from mise (aqua:github/copilot-cli). Authenticate once with
-- `copilot login` in a terminal; the plugin reuses those stored credentials.
--
-- No `dependencies`: agentic.nvim vendors its own UI and does not require
-- snacks, plenary, or nui.
return {
    "carlos-algms/agentic.nvim",
    opts = {
        provider = "copilot-acp",
    },
    -- Nested under <leader>a rather than a <leader>c/<leader>g of its own:
    -- <leader>a is already the AI group and <leader>g belongs to gitsigns.
    keys = {
        {
            "<leader>agg",
            function() require("agentic").toggle() end,
            mode = { "n", "v" },
            desc = "Toggle Copilot chat",
        },
        {
            "<leader>aga",
            function() require("agentic").add_selection_or_file_to_context() end,
            mode = { "n", "v" },
            desc = "Add selection or file to context",
        },
        {
            "<leader>agn",
            function() require("agentic").new_session() end,
            desc = "New Copilot session",
        },
        {
            "<leader>agr",
            function() require("agentic").restore_session() end,
            desc = "Restore Copilot session",
        },
    },
}
