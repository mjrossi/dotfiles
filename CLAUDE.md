# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

Personal dotfiles managed via symlinks. Two Python scripts (`install.py`, `uninstall.py`) create/remove symlinks from `~/.config/` and `~/` to this repo. No external Python dependencies — stdlib only, Python 3.10+.

## Package Management Policy

Split between `mise` and `brew`:

- **`mise`** — language runtimes and developer CLIs. Anything available via a mise backend (`cargo:`, `go:`, `pipx:`, `npm:`, native plugins) belongs here. Config: `mise/config.toml`.
- **`brew`** — only: `mise` (bootstrap), `fish` (login shell), GPG/macOS integration (`gnupg`, `pinentry-mac`), third-party taps, trivial unix utilities (`age`, `wget`, `p7zip`, `rename`, `telnet`, `wimlib`). Tracked in `Brewfile`.

When adding a tool: try `mise` first. Within mise, prefer prebuilt-binary backends (`aqua:`, native plugins) over source-build backends (`cargo:`, `go:`) unless source-building is the only option or a Go postinstall is needed — this keeps the global `rust` toolchain unnecessary and makes fresh-machine installs fast. Only use `brew` if it requires system integration or isn't available via any mise backend.

`install.py` runs `brew bundle install` (never `cleanup`) — additive only, leaves other brew packages alone. Skip with `--skip-brew` or `DOTFILES_SKIP_BREW=1`; no-ops when `brew` isn't on PATH.

## Commands

```bash
# Install dotfiles (creates symlinks)
./install.py
./install.py --dry-run --verbose   # preview without changes
./install.py --force               # no prompts

# Uninstall (removes symlinks, restores backups)
./uninstall.py

# Run all tests
python3 -m unittest discover tests -v

# Run a single test class
python3 -m unittest tests.test_install.TestFreshInstall -v

# Run a single test file
python3 tests/test_install.py
```

## Architecture

### Python scripts

- **`lib/common.py`** — all shared logic: `CONFIG_DIRS` and `CONFIG_FILES` dicts define what gets symlinked, `Logger`, `StateManager`, and helper functions (`backup_path`, `create_symlink`, `is_managed_symlink`, etc.)
- **`install.py`** — iterates `CONFIG_DIRS`/`CONFIG_FILES`, calls `process_item()` for each, then handles two special cases: SSH permissions fix and Zellij `config.kdl` generation
- **`uninstall.py`** — reads `.dotfiles-state`, removes managed symlinks, restores `.bak` backups, preserves machine-specific local files

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

`.dotfiles-state` (JSON, gitignored) records every installed symlink with its source, destination, backup path, and timestamp. `uninstall.py` uses this to know exactly what to remove.

### Zellij special case

Zellij doesn't support config includes. `install.py` always regenerates `config.kdl` by copying `config.shared.kdl` and appending `config.local.kdl` if it exists. Edit `config.shared.kdl` for shared keybindings; never edit `config.kdl` directly.
