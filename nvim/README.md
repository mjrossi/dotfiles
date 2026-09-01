# Neovim Configuration

Personal Neovim config using [lazy.nvim](https://github.com/folke/lazy.nvim) for plugin management and the native Neovim 0.11+ LSP API.

**Requirements:** Neovim 0.12+, [mise](https://mise.jdx.dev)

0.12 rather than 0.11 because `<leader>rs` uses the built-in `:lsp restart`; on 0.11 that command does not exist (it was `:LspRestart`, from nvim-lspconfig).

No native toolchain needed: the pickers shell out to `fd` and `ripgrep` (both from mise) and blink.cmp ships prebuilt binaries.

---

## Structure

```
nvim/
├── init.lua                        # Entry point — loads core and lazy
└── lua/mjrossi/
    ├── core/
    │   ├── init.lua                # Loads options, keymap, LspAttach
    │   ├── options.lua             # Vim options (tabs, line numbers, colors, etc.)
    │   └── keymap.lua              # Base keymaps (leader key, tabs, QoL)
    ├── lazy.lua                    # lazy.nvim bootstrap and plugin import
    ├── lsp/
    │   └── attach.lua              # LspAttach autocmd — buffer-local LSP keymaps
    └── plugins/
        ├── tokyonight.lua          # Color scheme
        ├── snacks.lua               # Picker (files, grep, buffers, help)
        ├── nvim-tree.lua           # File explorer
        ├── nvim-treesitter.lua     # Syntax highlighting/parsing
        ├── gitsigns.lua            # Git hunk indicators
        ├── nvim-surround.lua       # Surrounding text objects (ys, cs, ds)
        ├── nvim-autopairs.lua      # Auto-close brackets and quotes
        ├── fidget.lua              # LSP progress indicator (bottom-right)
        ├── nvim-lint.lua           # Async linting (rubocop, golangci-lint)
        ├── conform.lua             # Formatter chains + format-on-save
        ├── which-key.lua           # Keymap hint popup
        ├── claudecode.lua          # Claude Code AI integration
        ├── mise.lua                # Refreshes mise environment after :cd
        ├── ruby-lsp.lua            # mise-aware Ruby LSP lifecycle
        └── lsp/
            ├── nvim-lspconfig.lua  # LSP config — capabilities and per-server settings
            ├── mason.lua           # Language server + tool installer
            ├── lazydev.lua         # lazydev.nvim — Neovim Lua dev support
            └── blink-cmp.lua       # Completion engine (blink.cmp)
```

---

## Plugins

| Plugin | Purpose | Loads On |
|--------|---------|----------|
| tokyonight.nvim | Color scheme | startup |
| nvim-tree.lua | File explorer | `:NvimTree*` or `\nt`/`\nf` |
| nvim-treesitter | Syntax trees, highlight, indent | startup |
| gitsigns.nvim | Git hunk signs in gutter | BufReadPre/BufNewFile |
| nvim-surround | Add/change/delete surroundings | VeryLazy |
| nvim-autopairs | Auto-close `()`, `{}`, `""`, etc. | InsertEnter |
| fidget.nvim | LSP loading progress indicator | LspAttach |
| nvim-lint | Async linting via external tools | ft=go/ruby |
| conform.nvim | Formatter chains + format-on-save | BufWritePre |
| which-key.nvim | Keymap hint popup on `<leader>` | VeryLazy |
| mise.nvim | Re-applies mise env on `:cd` so LSP/tools stay correct per project | DirChanged / `:Mise` |
| ruby-lsp.nvim | Manages ruby-lsp gem per active Ruby version (mise-aware) | ft=ruby |
| claudecode.nvim | Claude Code terminal integration | keys |
| snacks.nvim | Picker (replaces telescope) + UI primitives for claudecode | startup |
| nvim-lspconfig | LSP server configurations | startup (see the note in the spec) |
| mason.nvim | Install/manage LSP servers and tools | startup |
| mason-lspconfig | Bridge mason ↔ lspconfig | with mason |
| mason-tool-installer | Install formatters/linters via mason | with mason |
| lazydev.nvim | Neovim Lua API completions | ft=lua |
| blink.cmp | Completion engine (LSP, path, snippets, buffer) | with nvim-lspconfig |

---

## Language Support

| Language | LSP Server | Formatter | Linter |
|----------|-----------|-----------|--------|
| Go | gopls | goimports | golangci-lint |
| Python | pyright + ruff | ruff | ruff (via LSP) |
| Ruby | ruby_lsp | rubocop | rubocop |
| Lua | lua_ls | stylua | — |
| YAML | yamlls | prettier | — |
| TOML | taplo | taplo | — |
| Rust (optional) | rust_analyzer | (LSP fallback) | — |
| Elixir (optional) | elixirls | (LSP fallback) | — |

**Notes:**
- Go: `goimports` handles both import organization and `gofmt` formatting
- Python: pyright does type checking, ruff does import sorting, formatting and linting. ruff's diagnostics come from its language server, so nvim-lint has no python entry; ruff's hover is disabled on attach so `K` returns pyright's type info. pyright uses the mise Python shim so it resolves to the correct version per `.mise.toml`
- Ruby: managed by `ruby-lsp.nvim` (not Mason) so the LSP gem matches the active mise Ruby version; rubocop diagnostics come from both ruby_lsp and nvim-lint
- Rust and Elixir: listed as optional recipes; their servers are not installed by this config. Install them through Mason and add the matching Treesitter parser when needed
- nvim-lint runs once when a Go/Ruby buffer loads and again after saves; it does not spawn linters on every `InsertLeave`
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
| `\rn` | Rename symbol |
| `\ca` | Code action (normal + visual) |
| `\rs` | Restart LSP (`:lsp restart`) |
| `gl` | Open diagnostics float |
| `[d` | Previous diagnostic |
| `]d` | Next diagnostic |
| `\q` | Diagnostics quickfix list |

### Find (Snacks picker)

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
| `\hu` | Unstage hunk (`stage_hunk` toggles) |
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

### Completion (blink.cmp)

| Key | Action |
|-----|--------|
| `<C-Space>` | Trigger completion |
| `<C-j>` | Next item |
| `<C-k>` | Previous item |
| `<CR>` | Confirm (no auto-select) |
| `<C-l>` | Confirm (auto-select) |
| `<C-e>` | Abort |
| `<C-b>` / `<C-f>` | Scroll docs |
| `<Tab>` / `<S-Tab>` | Next / previous snippet placeholder |

---

## Adding a New Language

1. **LSP server** — add to `mason_lspconfig.ensure_installed` in `lsp/mason.lua`
2. **Custom server config** (optional) — add `vim.lsp.config.<name> = { ... }` and `vim.lsp.enable("<name>")` in `lsp/nvim-lspconfig.lua`; otherwise mason's `automatic_enable` handles it with defaults + shared capabilities. Set only what differs from nvim-lspconfig's own `lsp/<name>.lua` — `cmd`, `filetypes` and `root_markers` are merged in already (`:h lsp-config`). Keymaps come from the `LspAttach` autocmd in `lsp/attach.lua`, not from an `on_attach` field
3. **Formatter** — add to `formatters_by_ft` in `plugins/conform.lua`; add the tool to `mason_tool_installer.ensure_installed` in `lsp/mason.lua`
4. **Linter** — add to `lint.linters_by_ft` in `plugins/nvim-lint.lua`; add the tool to `mason_tool_installer.ensure_installed` in `lsp/mason.lua`
5. **Treesitter parser** — add the language name to the `ensure_installed` list in `plugins/nvim-treesitter.lua`

---

## Useful Commands

| Command | Purpose |
|---------|---------|
| `:Lazy` | Plugin manager UI |
| `:Mason` | LSP/tool installer UI |
| `:checkhealth vim.lsp` | Show attached LSP clients and enabled configs |
| `:lsp restart` | Restart LSP clients for the current buffer |
| `:ConformInfo` | Show configured formatters for current buffer |
| `:checkhealth` | Diagnose configuration issues |
| `:TSInstall <lang>` | Manually install a treesitter parser |
