# Repository Guidelines

Guidance for coding agents working in this repository. `AGENTS.md` is a symlink
to this file, so Claude Code, Codex, and anything else that looks for either
name reads one document -- edit this one.

## What This Repo Is

Personal dotfiles managed via symlinks. Two Python scripts (`install.py`, `uninstall.py`) create/remove symlinks from `~/.config/` and `~/` to this repo. No external Python dependencies — stdlib only, Python 3.9+.

## Tool Ownership

Who installs what. These are defaults, not rules: when a tool fits better somewhere else, put it there and leave a one-line comment next to the entry saying why (the `Brewfile` and `mise/config.toml` already do this for their exceptions).

| Owner | Holds | Why |
|---|---|---|
| brew (`Brewfile`) | bootstrap (`mise`, `fish`); macOS/system integration (`1password-cli`, `ghostty`, `gnupg`, `pinentry-mac`, `r-app`); third-party taps; trivial unix utilities (`wget`, `p7zip`, `rename`, `telnet`, `wimlib`) | needs the OS, or has no mise backend |
| mise (`mise/config.toml`) | language runtimes and developer CLIs, prebuilt backends first (`aqua:`, `github:`, native plugins), then `pipx:`/`npm:`, and source builds (`go:`, `cargo:`) only when nothing prebuilt exists | per-project pins override this global fallback |
| mise Go postinstall (`install_go_tools` task) | `gopls`, `dlv` | link against the toolchain, so must be rebuilt per Go version |
| Mason (`nvim/lua/mjrossi/plugins/lsp/mason.lua`) | editor-only language servers and formatters, appended to Neovim's PATH | fallback when no project or mise copy exists |

Preferring prebuilt mise backends keeps the global `rust` toolchain unnecessary and makes fresh-machine installs fast. `mise/config.toml` is the *global* config: it holds tools wanted by default on every machine, and project-specific tools belong in that project's own mise config.

`install.py` runs `brew bundle check --no-upgrade` and, only if something is missing, `brew bundle install --no-upgrade` -- additive only: it installs what is missing, never upgrades what is merely outdated, and never runs `cleanup`, so other brew packages are left alone. Skip with `--skip-brew` or `DOTFILES_SKIP_BREW=1`; no-ops when `brew` isn't on PATH.

## Commands

```bash
# Install dotfiles (creates symlinks)
./install.py
./install.py --dry-run --verbose   # preview without changes
./install.py --skip-brew           # symlinks only, no brew bundle

# Uninstall (removes symlinks, restores backups)
./uninstall.py
./uninstall.py --force             # no confirmation prompts

# Run all tests
python3 -m unittest discover tests -v

# Run a single test class
python3 -m unittest tests.test_install.TestFreshInstall -v

# Run a single test file
python3 tests/test_install.py

# justfile shortcuts: test, lint (fish parse check + stylua --check nvim),
# install, dry-run, completions (regenerate CLI-snapshot fish completions)
just --list
```

## Architecture

### Python scripts

- **`lib/common.py`** — all shared logic: `CONFIG_DIRS` and `CONFIG_FILES` dicts define what gets symlinked, `Logger`, `StateManager`, and helper functions (`backup_path`, `create_symlink`, `is_managed_symlink`, etc.)
- **`install.py`** — iterates `CONFIG_DIRS`/`CONFIG_FILES`, calls `process_item()` for each, then fixes SSH permissions, generates Zellij `config.kdl`, and installs missing Brewfile entries (`--no-upgrade`, see above)
- **`uninstall.py`** — reads `.dotfiles-state`, removes managed symlinks, restores the exact recorded backup, and preserves machine-specific local files

**To add a new dotfile**, update `CONFIG_DIRS` or `CONFIG_FILES` in `lib/common.py` and add the source directory/file to the repo.

### Symlink targets

| Repo path | Symlinked to |
|---|---|
| `fish/` | `~/.config/fish/` |
| `nvim/` | `~/.config/nvim/` |
| `zellij/` | `~/.config/zellij/` |
| `mise/` | `~/.config/mise/` |
| `ghostty/` | `~/.config/ghostty/` |
| `gitconfig` | `~/.gitconfig` |
| `gitignore_global` | `~/.gitignore_global` |
| `ssh/config` | `~/.ssh/config` |

### Machine-specific / local files (not tracked in git)

- `~/.gitconfig.local` — email and SSH signing key (included by `gitconfig`)
- `~/.config/fish/config.local.fish` — sourced by `config.fish` if it exists
- `~/.config/zellij/config.local.kdl` — appended to generated `config.kdl` by `install.py`
- `zellij/config.kdl` — regenerated on every `install.py` run from `config.shared.kdl` + local override

### State tracking

`.dotfiles-state` (JSON, gitignored) records every installed symlink with its source, destination, exact backup path (or `null`), and timestamp. `uninstall.py` uses this to know exactly what to remove and restore. Version 1.0 state files only contain `backup_created`; `StateManager.load()` upgrades those records once by discovering the newest `.bak` and recording its path, so everything downstream deals with 1.1 records only. On install, records for sources no longer in `CONFIG_DIRS`/`CONFIG_FILES` are dropped, unless their destination still links into the repo (uninstall still needs those). With no state, uninstall removes managed symlinks but leaves backups untouched rather than guessing ownership.

### Fish startup layout

Startup config lives in `fish/conf.d/`, which fish sources **before** `config.fish`, sorted by filename. All of the user's `conf.d` runs before any system or vendor `vendor_conf.d` snippet, which is what lets `25-mise.fish` switch off Homebrew's mise activation. The numeric prefixes encode a dependency order, so a new fragment goes at the position its dependencies allow, not just at the end:

| File | Runs | Holds |
|---|---|---|
| `00-homebrew.fish` | always | Homebrew env, before anything that needs brew paths |
| `10-paths.fish` | always | `~/.local/bin`, prepended after Homebrew so it wins |
| `20-env.fish` | always | `EDITOR`, `SSH_AUTH_SOCK` |
| `25-mise.fish` | always | `mise activate` when interactive, shims dir on PATH otherwise; disables Homebrew's `vendor_conf.d/mise-activate.fish` |
| `30-interactive.fish` | interactive only | colours, abbreviations, `GPG_TTY` |

`config.fish` itself holds only the `config.local.fish` include, which must run last so it can override everything above.

GitHub credentials are intentionally on demand: `github-pat` reads the MCP token from 1Password via `op read` only when requested, and `gh` uses its own stored authentication without exporting `GITHUB_TOKEN` on every shell's first prompt.

Three rules that are easy to get wrong:

- **Anything a script, editor, or launchd job needs goes in `20-env.fish`**, outside the `status is-interactive; or exit` guard in `30-interactive.fish`. Everything else belongs behind that guard — a `tty` call or a colour variable costs a process spawn or does nothing in `fish -c`.
- **Non-interactive shells get mise through shims only** (`25-mise.fish`). Tool versions still resolve per directory, but mise `[env]` values are not set there, so anything a script needs belongs in `20-env.fish`, not in mise `[env]`.
- **`00-homebrew.fish` is a hand transcription of `brew shellenv fish`**, inlined because shelling out cost ~21ms on every shell start to print constant output. Regenerate it from `brew shellenv fish` if Homebrew changes what it exports; don't hand-edit the exports.

Prefer `set -g` over the default universal scope for path variables. A universal `fish_user_paths` is written into `fish_variables` and then applies forever regardless of what this repo says — that is how `~/.local/bin` previously ended up ordered by accident, silently turning `config.fish`'s own `fish_add_path` into a no-op.

### Zellij special case

Zellij doesn't support config includes. `install.py` always regenerates `config.kdl` by copying `config.shared.kdl` and appending `config.local.kdl` if it exists. Edit `config.shared.kdl` for shared options; never edit `config.kdl` directly.

`config.shared.kdl` holds **options only** — no `keybinds` block. Zellij's default keybindings are inherited wholesale so that each release's new bindings arrive automatically. It previously carried `keybinds clear-defaults=true` plus a verbatim copy of the defaults, which froze the keymap at the version it was copied from and silently suppressed everything added since. Only add a `keybinds` block for a binding that genuinely differs from upstream, and never with `clear-defaults=true`.
