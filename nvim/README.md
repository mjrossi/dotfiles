# Neovim Configuration

Personal Neovim config using [lazy.nvim](https://github.com/folke/lazy.nvim) for plugin management and the native Neovim 0.11+ LSP API.

**Requirements:** Neovim 0.11+, `make` + C compiler (for telescope-fzf-native), [mise](https://mise.jdx.dev)

---

## Structure

```
nvim/
├── init.lua                        # Entry point — loads core and lazy
└── lua/mjrossi/
    ├── core/
    │   ├── init.lua                # Loads options and keymap
    │   ├── options.lua             # Vim options (tabs, line numbers, colors, etc.)
    │   └── keymap.lua              # Base keymaps (leader key, tabs, QoL)
    ├── lazy.lua                    # lazy.nvim bootstrap and plugin import
    └── plugins/
        ├── tokyonight.lua          # Color scheme
        ├── nvim-tree.lua           # File explorer
        ├── telescope.lua           # Fuzzy finder (+ fzf-native)
        ├── nvim-treesitter.lua     # Syntax highlighting/parsing
        ├── gitsigns.lua            # Git hunk indicators
        ├── nvim-surround.lua       # Surrounding text objects (ys, cs, ds)
        ├── nvim-autopairs.lua      # Auto-close brackets and quotes
        ├── fidget.lua              # LSP progress indicator (bottom-right)
        ├── nvim-lint.lua           # Async linting (pylint, rubocop, golangci-lint)
        ├── conform.lua             # Formatter chains + format-on-save
        ├── which-key.lua           # Keymap hint popup
        ├── claudecode.lua          # Claude Code AI integration
        └── lsp/
            ├── lsp-zero.lua        # LSP config — capabilities, on_attach, server configs
            ├── mason.lua           # Language server + tool installer
            ├── neodev.lua          # lazydev.nvim — Neovim Lua dev support
            └── nvim-cmp.lua        # Completion engine (nvim-cmp + LuaSnip)
```

---

## Plugins

| Plugin | Purpose | Loads On |
|--------|---------|----------|
| tokyonight.nvim | Color scheme | startup |
| nvim-tree.lua | File explorer | startup |
| telescope.nvim | Fuzzy finder | command |
| telescope-fzf-native | Faster fzf sorting for telescope | with telescope |
| nvim-treesitter | Syntax trees, highlight, indent | startup |
| gitsigns.nvim | Git hunk signs in gutter | BufReadPre/BufNewFile |
| nvim-surround | Add/change/delete surroundings | VeryLazy |
| nvim-autopairs | Auto-close `()`, `{}`, `""`, etc. | InsertEnter |
| fidget.nvim | LSP loading progress indicator | startup |
| nvim-lint | Async linting via external tools | BufReadPre/BufNewFile |
| conform.nvim | Formatter chains + format-on-save | BufWritePre |
| which-key.nvim | Keymap hint popup on `<leader>` | VeryLazy |
| mise.nvim | Re-applies mise env on `:cd` so LSP/tools stay correct per project | startup |
| ruby-lsp.nvim | Manages ruby-lsp gem per active Ruby version (mise-aware) | ft=ruby |
| claudecode.nvim | Claude Code terminal integration | keys |
| snacks.nvim | UI primitives (required by claudecode) | startup |
| nvim-lspconfig | LSP server configurations | BufReadPre/BufNewFile |
| mason.nvim | Install/manage LSP servers and tools | startup |
| mason-lspconfig | Bridge mason ↔ lspconfig | with mason |
| mason-tool-installer | Install formatters/linters via mason | with mason |
| lazydev.nvim | Neovim Lua API completions | ft=lua |
| nvim-cmp | Completion engine | InsertEnter |
| LuaSnip | Snippet engine | with nvim-cmp |

---

## Language Support

| Language | LSP Server | Formatter | Linter |
|----------|-----------|-----------|--------|
| Go | gopls | goimports | golangci-lint |
| Python | pyright | isort → black | pylint |
| Ruby | ruby_lsp | rubocop | rubocop |
| Lua | lua_ls | stylua | — |
| YAML | yamlls | prettier | — |
| TOML | taplo | taplo | — |
| Rust | rust_analyzer | (LSP fallback) | — |
| Elixir | elixirls | (LSP fallback) | — |

**Notes:**
- Go: `goimports` handles both import organization and `gofmt` formatting
- Python: `isort` runs before `black` to organize imports first; pyright uses the mise Python shim so it resolves to the correct version per `.mise.toml`
- Ruby: managed by `ruby-lsp.nvim` (not Mason) so the LSP gem matches the active mise Ruby version; rubocop diagnostics come from both ruby_lsp and nvim-lint
- golangci-lint: uses defaults if no `.golangci.yml` present in project root
- mise shims are prepended to `PATH` at startup — tools resolve to the correct project version even when Neovim is launched from a GUI

---

## Keybindings

Leader key: `\`

### Core

| Key | Action |
|-----|--------|
| `<left>` | Previous tab |
| `<right>` | Next tab |
| `\nh` | Clear search highlight |
| `Y` | Yank to end of line |
| `x` + `p` (visual) | Paste without yanking |
| `x` + `*` (visual) | Search current selection |

### LSP

| Key | Action |
|-----|--------|
| `gd` | Go to definition |
| `gr` | Find references |
| `gD` | Go to declaration |
| `gi` | Go to implementation |
| `gt` | Go to type definition |
| `K` | Hover documentation |
| `\rn` | Rename symbol |
| `\ca` | Code action (normal + visual) |
| `\rs` | Restart LSP |
| `gl` | Open diagnostics float |
| `[d` | Previous diagnostic |
| `]d` | Next diagnostic |
| `\q` | Diagnostics quickfix list |

### Find (Telescope)

| Key | Action |
|-----|--------|
| `\ff` | Find files |
| `\fg` | Live grep |
| `\fb` | Find buffers |
| `\fh` | Find help tags |
| `\fw` | Find word under cursor |

### Git (Gitsigns)

| Key | Action |
|-----|--------|
| `]h` | Next hunk |
| `[h` | Previous hunk |
| `\hs` | Stage hunk |
| `\hr` | Reset hunk |
| `\hS` | Stage buffer |
| `\hu` | Undo stage hunk |
| `\hR` | Reset buffer |
| `\gp` | Preview hunk |
| `\gb` | Blame line |
| `\gd` | Diff this |
| `\gD` | Diff this ~ |

### Nav / NvimTree

| Key | Action |
|-----|--------|
| `\nt` | Toggle file tree |
| `\nf` | Reveal current file in tree |

### Code / Formatting

| Key | Action |
|-----|--------|
| `\cf` | Format buffer (async) |

### AI / Claude

| Key | Action |
|-----|--------|
| `\ac` | Toggle Claude Code |
| `\af` | Focus Claude Code |
| `\ar` | Resume Claude (`--resume`) |
| `\aC` | Continue Claude (`--continue`) |
| `\ab` | Add current buffer to Claude |
| `\as` (visual) | Send selection to Claude |
| `\as` (NvimTree) | Add file to Claude |
| `\aa` | Accept diff |
| `\ad` | Deny diff |

### Completion (nvim-cmp)

| Key | Action |
|-----|--------|
| `<C-Space>` | Trigger completion |
| `<C-j>` | Next item |
| `<C-k>` | Previous item |
| `<CR>` | Confirm (no auto-select) |
| `<C-l>` | Confirm (auto-select) |
| `<C-e>` | Abort |
| `<C-b>` / `<C-f>` | Scroll docs |

---

## Adding a New Language

1. **LSP server** — add to `mason_lspconfig.ensure_installed` in `lsp/mason.lua`
2. **Custom server config** (optional) — add `vim.lsp.config.<name> = { ... }` and `vim.lsp.enable("<name>")` in `lsp/lsp-zero.lua`; otherwise mason's `automatic_enable = true` handles it with defaults + shared capabilities/on_attach
3. **Formatter** — add to `formatters_by_ft` in `plugins/conform.lua`; add the tool to `mason_tool_installer.ensure_installed` in `lsp/mason.lua`
4. **Linter** — add to `lint.linters_by_ft` in `plugins/nvim-lint.lua`; add the tool to `mason_tool_installer.ensure_installed` in `lsp/mason.lua`
5. **Treesitter parser** — add the language name to the `ensure_installed` list in `plugins/nvim-treesitter.lua`

---

## Useful Commands

| Command | Purpose |
|---------|---------|
| `:Lazy` | Plugin manager UI |
| `:Mason` | LSP/tool installer UI |
| `:LspInfo` | Show attached LSP clients for current buffer |
| `:ConformInfo` | Show configured formatters for current buffer |
| `:checkhealth` | Diagnose configuration issues |
| `:TSInstall <lang>` | Manually install a treesitter parser |
