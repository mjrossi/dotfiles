# Dotfiles

[![tests](https://github.com/mjrossi/dotfiles/actions/workflows/tests.yml/badge.svg)](https://github.com/mjrossi/dotfiles/actions/workflows/tests.yml)

Personal configuration for Fish, Neovim, Zellij, Ghostty, mise, Git, and SSH, managed via symlinks into `~/.config/` and `~/`. Two Python scripts (`install.py`, `uninstall.py`) wire it up. Stdlib only — Python 3.10+.

## Quick start

```bash
git clone <your-repo-url> ~/dotfiles
cd ~/dotfiles
./install.py                  # see `./install.py --help` for flags
```

On the first install, set up machine-local files (all gitignored):

```bash
# Required — email + SSH signing key for commits
cp gitconfig.local.template ~/.gitconfig.local
nvim ~/.gitconfig.local

# Optional — work-specific env vars / abbreviations
cp fish/config.local.fish.template ~/.config/fish/config.local.fish

# Optional — zellij overrides (cert paths, etc.). Appended to the generated
# ~/.config/zellij/config.kdl on every install.py run.
nvim ~/.config/zellij/config.local.kdl  # then re-run ./install.py
```

Then restart your shell (`exec $SHELL`) and open `nvim` once to initialize plugins.

## Uninstall

```bash
./uninstall.py
```

Removes only symlinks that point back into this repo, restores any `.bak` backups created by `install.py`, and copies preserved machine-local files (`fish/config.local.fish`, `zellij/config.kdl`) back into the restored directories.

## Package management

Global tooling splits between `mise` and `brew`:

- **`mise`** — language runtimes and developer CLIs (anything installable via `cargo:`, `go:`, `pipx:`, `npm:`, or a native/aqua plugin). Config in `mise/config.toml`.
- **`brew`** — only what can't live in mise cleanly: `mise` itself (bootstrap), `fish` (login shell), GPG/macOS integration (`gnupg`, `pinentry-mac`), third-party taps, a handful of trivial unix utilities. Tracked in `Brewfile`.

`install.py` runs `brew bundle` against the committed `Brewfile` — additive only, never `cleanup`, so ad-hoc brew installs are left alone. Skip with `--skip-brew` or `DOTFILES_SKIP_BREW=1`; no-ops when `brew` isn't on PATH.

## Architecture

For code-level details (how the symlink/backup/state machinery works, how to add a new dotfile), see [CLAUDE.md](./CLAUDE.md).

## Tests

```bash
python3 -m unittest discover tests -v
```
