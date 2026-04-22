# Dotfiles

[![tests](https://github.com/mjrossi/dotfiles/actions/workflows/tests.yml/badge.svg)](https://github.com/mjrossi/dotfiles/actions/workflows/tests.yml)

Personal configuration files managed via symlinks. This repository contains configurations for Fish shell, Neovim, Zellij, Ghostty, mise, Git, and SSH, with Python scripts to automatically install and manage them across machines.

## What's Included

- **Fish Shell** - Shell configuration, custom prompt, and functions
- **Neovim** - Editor configuration with LSP, Tree-sitter, and plugins (lazy.nvim)
- **Zellij** - Terminal multiplexer configuration
- **Ghostty** - Terminal emulator configuration (Tokyo Night theme)
- **mise** - Runtime version manager configuration
- **Brewfile** - Minimal Homebrew footprint (bootstrap + system integration only)
- **Git** - Global gitconfig and gitignore
- **SSH** - SSH config with 1Password agent integration

## Package Management Policy

Global tooling is split between `mise` and `brew`:

- **`mise` owns** language runtimes and developer CLIs — anything version-sensitive or installable via a mise backend (`cargo:`, `go:`, `pipx:`, `npm:`, native plugins). Config lives in `mise/config.toml`.
- **`brew` owns** only what can't live in mise cleanly: `mise` itself (bootstrap), `fish` (login shell), GPG/macOS integration (`gnupg`, `pinentry-mac`), third-party taps, and a handful of trivial unix utilities. Tracked in `Brewfile`.

`install.py` runs `brew bundle` against the committed `Brewfile` — it only installs what's missing and **never** removes packages not listed, so other tools installed ad-hoc on a machine are left alone. Skip with `--skip-brew` or `DOTFILES_SKIP_BREW=1` (or simply run on a machine without Homebrew — it no-ops).

## Quick Start

### Installation

1. Clone this repository:
   ```bash
   git clone <your-repo-url> ~/dotfiles
   cd ~/dotfiles
   ```

2. Run the installation script:
   ```bash
   ./install.py
   ```

3. Set up machine-specific configurations:
   ```bash
   # Git (required)
   cp ~/dotfiles/gitconfig.local.template ~/.gitconfig.local
   nvim ~/.gitconfig.local  # Add your email and signing key

   # Fish (optional - only if you need machine-specific settings)
   cp ~/dotfiles/fish/config.local.fish.template ~/.config/fish/config.local.fish
   nvim ~/.config/fish/config.local.fish

   # Zellij (automatically created by install.py from config.shared.kdl)
   # Edit if you need machine-specific settings like cert paths
   nvim ~/.config/zellij/config.kdl
   ```

4. Restart your shell or source the new configuration:
   ```bash
   exec $SHELL
   ```

5. Open Neovim to initialize plugins (first run only):
   ```bash
   nvim
   ```

### Uninstallation

To remove symlinks and restore backups:
```bash
./uninstall.py
```

**Machine-specific files are preserved:**
- `fish/config.local.fish` → copied to `~/.config/fish/`
- `zellij/config.kdl` → copied to `~/.config/zellij/`
- `~/.gitconfig.local` → already in home directory (not affected)

The script automatically detects and preserves these files during uninstallation. If no backup exists (fresh machine), the directories are created before copying the preserved files.

## How It Works

The installation script creates **symlinks** from your home directory to this repository:

```
~/.config/fish/       → ~/dotfiles/fish/
~/.config/nvim/       → ~/dotfiles/nvim/
~/.config/zellij/     → ~/dotfiles/zellij/
~/.config/mise/       → ~/dotfiles/mise/
~/.config/ghostty/    → ~/dotfiles/ghostty/
~/.gitconfig          → ~/dotfiles/gitconfig
~/.gitignore_global   → ~/dotfiles/gitignore_global
~/.ssh/config         → ~/dotfiles/ssh/config
```

**Benefits:**
- Edit files in this repo and changes are immediately active
- Keep all configs in sync via git
- Easy to track changes and revert if needed

## Machine-Specific Configuration

Some configurations need to be customized per machine (work vs personal, different paths, etc.). These use template files and local configs that are **not tracked in git**.

### Git Configuration

The `gitconfig` file contains shared settings across all machines, but email and SSH signing keys are machine-specific.

**Setup on a new machine:**

1. Copy the template:
   ```bash
   cp ~/dotfiles/gitconfig.local.template ~/.gitconfig.local
   ```

2. Edit `~/.gitconfig.local` with your machine-specific settings:
   ```bash
   nvim ~/.gitconfig.local
   ```

3. Update the email and signing key:
   - **Email**: Your work or personal email for this machine
   - **Signing key**: Your SSH public key from 1Password
     - Open 1Password → SSH key → "Configure Commit Signing" to get the key

**Example `~/.gitconfig.local`:**
```gitconfig
[user]
  email = your.email@example.com
  signingkey = ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPgH...
```

**How it works:**
- The main `gitconfig` includes `~/.gitconfig.local` via `[include]`
- Each machine has its own `~/.gitconfig.local` with machine-specific email/key
- Commit signing uses 1Password's SSH agent (no GPG required)

### Fish Shell Configuration

The main `config.fish` is shared across machines, but machine-specific settings (environment variables, work-specific configs) go in a local file.

**Setup on a new machine:**

1. Create your local config (optional - only if you need machine-specific settings):
   ```bash
   cp ~/dotfiles/fish/config.local.fish.template ~/.config/fish/config.local.fish
   ```

2. Edit with your machine-specific settings:
   ```bash
   nvim ~/.config/fish/config.local.fish
   ```

**Example `~/.config/fish/config.local.fish`:**
```fish
# Work-specific environment variables
set -gx WORK_PROXY "proxy.example.com:8080"

# Machine-specific abbreviations
abbr work 'cd ~/work-projects'
```

**How it works:**
- The main `config.fish` automatically sources `~/.config/fish/config.local.fish` if it exists
- Add any machine-specific environment variables, abbreviations, or functions there

### Zellij Configuration

Zellij doesn't support config includes, so we use a shared config with an optional local overlay.

**How it works:**
- The entire `~/.config/zellij/` directory is symlinked to `~/dotfiles/zellij/`
- `config.shared.kdl` contains all shared keybindings and settings (tracked in git)
- `config.kdl` is **regenerated on every `./install.py` run** from `config.shared.kdl` (not tracked in git)
- If `config.local.kdl` exists, it is appended to the generated `config.kdl`

**Adding machine-specific settings (e.g., cert paths):**

Create `~/.config/zellij/config.local.kdl` with your overrides:

```bash
nvim ~/.config/zellij/config.local.kdl
```

Then re-run `./install.py` to regenerate `config.kdl` with your local settings appended.

## Scripts

### install.py

Installs dotfiles by creating symlinks to this repository.

**Usage:**
```bash
./install.py [options]
```

**Options:**
- `--dry-run` - Preview changes without making them
- `--verbose` - Show detailed debug output
- `--force` - Override prompts and proceed automatically
- `--skip-brew` - Skip the Brewfile step (also: `DOTFILES_SKIP_BREW=1`)

**What it does:**
1. Backs up any existing files/directories with `.bak` suffix
2. Creates symlinks from your home directory to this repo
3. Installs anything missing from the `Brewfile` (idempotent; skipped silently if `brew` isn't on PATH)
4. Tracks installation state in `.dotfiles-state` (JSON)

**Examples:**
```bash
# Standard installation
./install.py

# Preview what would happen
./install.py --dry-run

# See detailed output
./install.py --verbose

# Install without prompts
./install.py --force

# Combine flags
./install.py --dry-run --verbose
```

### uninstall.py

Removes symlinks and optionally restores backups.

**Usage:**
```bash
./uninstall.py [options]
```

**Options:**
- `--dry-run` - Preview changes without making them
- `--verbose` - Show detailed debug output
- `--force` - Override prompts and proceed automatically

**What it does:**
1. Detects and preserves machine-specific configuration files
2. Removes symlinks that point to this repository
3. Restores `.bak` backup files if they exist
4. Copies preserved machine-specific files into restored directories
5. Optionally removes the `.dotfiles-state` file

**Safety:**
- Only removes symlinks that point to this repository
- Never removes files or directories that aren't symlinks
- Preserves machine-specific `.local` and config files
- Asks for confirmation before proceeding

## File Structure

```
dotfiles/
├── .gitignore                     # Excludes auto-generated files
├── README.md                      # This file
├── install.py                     # Installation script
├── uninstall.py                   # Uninstallation script
├── lib/
│   ├── __init__.py               # Python package marker
│   └── common.py                 # Shared functions and configuration
├── fish/                          # Fish shell configuration
│   ├── config.fish               # Main Fish config (sources config.local.fish)
│   ├── config.local.fish.template # Template for machine-specific config
│   ├── functions/                # Custom functions
│   └── completions/              # Custom completions
├── nvim/                          # Neovim configuration
│   ├── init.lua                  # Main entry point
│   └── lua/mjrossi/              # Modular config
├── zellij/                        # Zellij configuration
│   └── config.shared.kdl         # Shared config (tracked in git)
│   # config.kdl generated by install.py; config.local.kdl for overrides (both gitignored)
├── mise/                          # mise configuration
│   └── config.toml
├── ghostty/                       # Ghostty terminal configuration
│   └── config
├── ssh/                           # SSH configuration
│   └── config                    # 1Password SSH agent integration
├── gitconfig                      # Git global config
├── gitconfig.local.template       # Template for machine-specific git config
└── gitignore_global               # Git global ignore patterns
```

## Auto-Generated Files

Some files are automatically generated by the tools themselves and should **not** be checked into git:

- `fish/fish_variables` - Fish shell state (auto-generated)
- `nvim/lazy-lock.json` - Neovim plugin versions (auto-generated by lazy.nvim)
- `fish/conf.d/fish_frozen_*.fish` - Fish migration files (auto-generated)

These are excluded via `.gitignore` and will be created automatically when you use the tools after installation.

## Machine-Specific Files

Some files contain machine-specific settings and should **not** be checked into git:

- `~/.gitconfig.local` - Machine-specific git configuration (email, signing key)
- `~/.config/fish/config.local.fish` - Machine-specific Fish shell configuration
- `~/.config/zellij/config.local.kdl` - Machine-specific Zellij overrides (appended to generated `config.kdl`)

## Adding New Dotfiles

To add new configuration files or directories:

1. **Add to this repository:**
   ```bash
   cp -r ~/.config/tool ~/dotfiles/tool
   git add tool/
   git commit -m "Add tool configuration"
   ```

2. **Update `lib/common.py`:**

   For directories (in `~/.config/`):
   ```python
   CONFIG_DIRS: Dict[str, Path] = {
       'fish': Path.home() / '.config' / 'fish',
       'tool': Path.home() / '.config' / 'tool',  # Add this line
       # ...
   }
   ```

   For files (in `~/`):
   ```python
   CONFIG_FILES: Dict[str, Path] = {
       'gitconfig': Path.home() / '.gitconfig',
       'toolrc': Path.home() / '.toolrc',  # Add this line
       # ...
   }
   ```

3. **Run the installation script:**
   ```bash
   ./install.py
   ```

## Requirements

- **Python 3.6+** (for f-strings and pathlib)
- Standard library only - no external dependencies

Python 3 comes pre-installed on macOS and most modern Linux distributions.

## Idempotency

Both scripts are **idempotent** - safe to run multiple times:

- `install.py` will skip items that are already correctly symlinked
- `uninstall.py` will only remove symlinks that point to this repository
- Running either script multiple times won't cause problems

## Backup System

**Automatic Backups:**
- Existing files/directories are renamed with `.bak` suffix
- If `.bak` already exists, uses `.bak.1`, `.bak.2`, etc.
- Backups are restored when running `uninstall.py`

**Example:**
```bash
# Before install
~/.config/fish/           # Your existing config

# After install
~/.config/fish/           # Symlink to ~/dotfiles/fish/
~/.config/fish.bak/       # Your original config (backed up)

# After uninstall
~/.config/fish/           # Restored from backup
```

## State Tracking

The installation script creates `.dotfiles-state` (JSON format) to track:
- What was installed
- Where backups were created
- Timestamps

This file helps `uninstall.py` know exactly what to remove. It's excluded from git via `.gitignore`.

## Troubleshooting

### Permission Denied

```bash
chmod +x install.py uninstall.py
```

### Script Not Found

Ensure you're in the dotfiles directory:
```bash
cd ~/dotfiles
./install.py
```

Or use Python directly:
```bash
python3 install.py
```

### See What Would Happen

Use `--dry-run --verbose` to preview without making changes:
```bash
./install.py --dry-run --verbose
```

### Remove Everything

To completely remove all symlinks and restore original configs:
```bash
./uninstall.py
# Answer 'y' to remove state file
```

### Manual Removal

If something goes wrong, you can manually remove symlinks:
```bash
# Check if it's a symlink
ls -la ~/.config/fish

# Remove symlink
rm ~/.config/fish

# Restore backup
mv ~/.config/fish.bak ~/.config/fish
```

## Development

The codebase is organized for maintainability:

- **`lib/common.py`** - Shared configuration and utility functions
- **`install.py`** - Installation logic
- **`uninstall.py`** - Uninstallation logic
- **`tests/`** - Unit tests for install and uninstall scripts

All scripts use:
- Type hints for documentation
- Clear function names and docstrings
- Comprehensive error handling
- Colored output for readability

### Running Tests

Run the test suite to verify installation and uninstallation logic:

```bash
./run_tests.sh
```

Or run specific tests:
```bash
python3 tests/test_install.py
python3 tests/test_uninstall.py
```

The tests cover:
- Fresh machine installation (no existing configs)
- Installation with existing configs (backup creation)
- Idempotent re-runs (skipping already installed)
- Zellij config.kdl creation from config.shared.kdl
- State file preservation on re-install
- SSH directory permission handling
- Uninstallation with and without backups
- Machine-specific file preservation
- Dry-run mode behavior

## License

Personal configuration files - use at your own risk!
