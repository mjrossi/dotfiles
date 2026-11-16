# Task runner for this repo. `just` with no arguments lists the recipes.

# stylua is the formatter conform runs on every Lua save. It is installed by
# Mason, whose bin dir is only on Neovim's PATH, so fall back to it when no
# stylua is on the shell's PATH (CI installs one through mise).
stylua := `command -v stylua || echo "$HOME/.local/share/nvim/mason/bin/stylua"`

default:
    @just --list

# Run the installer test suite (temp dirs only; never touches $HOME)
test:
    python3 -m unittest discover tests -v

# Parse-check every fish file and check Lua formatting against nvim/.stylua.toml
lint:
    #!/usr/bin/env bash
    set -euo pipefail
    # fish --no-execute takes one script; anything after it is that script's
    # arguments, so each file needs its own call.
    for f in fish/config.fish fish/conf.d/*.fish fish/functions/*.fish fish/completions/*.fish; do
        fish --no-execute "$f"
    done
    "{{ stylua }}" --check nvim

# Install the dotfiles; extra flags go to install.py (e.g. `just install --skip-brew`)
install *args:
    ./install.py {{ args }}

# Preview what install.py would do, without changing anything
dry-run:
    ./install.py --dry-run --verbose

# These completions are snapshots of each CLI's own output and go stale as
# the CLIs change. Review the diff before committing: copilot.fish in
# particular was last committed in a different shape from what current
# `copilot completion fish` prints.
#
# Regenerate the copilot and docker fish completions from the CLIs
completions:
    copilot completion fish > fish/completions/copilot.fish
    docker completion fish > fish/completions/docker.fish
