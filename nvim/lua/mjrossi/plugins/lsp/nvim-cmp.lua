return {
    "hrsh7th/nvim-cmp",
    lazy = true,
    dependencies = { "L3MON4D3/LuaSnip" },
    config = function()
        local cmp = require("cmp")
        cmp.setup({
            mapping = cmp.mapping.preset.insert({
                ["<C-j>"] = cmp.mapping.select_next_item(),
                ["<C-k>"] = cmp.mapping.select_prev_item(),
                ["<C-l>"] = cmp.mapping.confirm({ select = true }),
            })
        })
    end
}
