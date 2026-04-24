#!/usr/bin/env python3
"""
Dotfiles installation script - creates symlinks for configuration files and directories.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Import from lib.common
from lib.common import (
    CONFIG_DIRS, CONFIG_FILES, Logger, StateManager,
    get_dotfiles_dir, backup_path, create_symlink, is_managed_symlink
)


def process_item(source_name, dest, kind, dotfiles_dir, state, args, logger, counters):
    """Process a single config item: validate, backup if needed, and create symlink."""
    source = dotfiles_dir / source_name

    logger.header(f"Installing {source_name}...")
    logger.debug(f"Processing {kind}: {source_name}")
    logger.debug(f"  Source: {source}")
    logger.debug(f"  Destination: {dest}")

    # Validate source exists and is the right type
    if not source.exists():
        logger.error(f"Source {kind} does not exist: {source}", indent=True)
        counters['errors'] += 1
        return

    if kind == 'dir' and not source.is_dir():
        logger.error(f"Source is not a directory: {source}", indent=True)
        counters['errors'] += 1
        return

    if kind == 'file' and not source.is_file():
        logger.error(f"Source is not a file: {source}", indent=True)
        counters['errors'] += 1
        return

    had_backup = False

    # Check destination status
    if dest.exists() or dest.is_symlink():
        if is_managed_symlink(dest, dotfiles_dir):
            target = dest.readlink()
            if not target.is_absolute():
                target = (dest.parent / target).resolve()
            if target == source:
                logger.debug(f"Already installed: {source_name}")
                logger.info("Skipped (already installed)", indent=True)
                counters['skipped'] += 1
                return
            else:
                logger.warning(f"Symlink exists but points to different location: {dest} -> {target}", indent=True)

        if dest.exists() and not dest.is_symlink():
            if kind == 'dir' and dest.is_file():
                logger.error("Destination is a file, cannot replace with directory", indent=True)
                counters['errors'] += 1
                return

            if kind == 'file' and dest.is_dir():
                logger.error("Destination is a directory, cannot replace with file", indent=True)
                counters['errors'] += 1
                return

            backup = backup_path(dest, dry_run=args.dry_run, logger=logger)
            had_backup = bool(backup)
            if backup:
                counters['backed_up'] += 1
                label = "directory" if kind == 'dir' else "file"
                logger.success(f"Backed up existing {label}", indent=True)

        elif dest.is_symlink() and not dest.exists():
            logger.warning("Removing broken symlink", indent=True)
            if not args.dry_run:
                dest.unlink()

    # Create symlink
    logger.debug(f"Creating symlink: {dest} -> {source}")
    if create_symlink(source, dest, dry_run=args.dry_run, logger=logger):
        logger.success("Created symlink", indent=True)
        counters['installed'] += 1
        if not args.dry_run:
            state.add(kind, source_name, dest, backup_created=had_backup)
    else:
        counters['errors'] += 1


def fix_ssh_permissions(ssh_dir, dry_run, logger):
    """Ensure ~/.ssh is 700 and ~/.ssh/config is 600. No-op when already correct."""
    if not ssh_dir.exists():
        return

    current_perms = oct(ssh_dir.stat().st_mode)[-3:]
    if current_perms != '700':
        logger.debug(f"Fixing ~/.ssh permissions: {current_perms} -> 700")
        if not dry_run:
            os.chmod(ssh_dir, 0o700)
        logger.success("Set ~/.ssh directory permissions to 700", indent=True)

    ssh_config = ssh_dir / 'config'
    if ssh_config.exists() or ssh_config.is_symlink():
        config_perms = oct(os.stat(ssh_config).st_mode)[-3:]
        if config_perms != '600':
            logger.debug(f"Fixing ~/.ssh/config permissions: {config_perms} -> 600")
            if not dry_run:
                os.chmod(ssh_config, 0o600)
            logger.success("Set ~/.ssh/config permissions to 600", indent=True)


def generate_zellij_config(zellij_config_dir, dry_run, logger):
    """Regenerate zellij config.kdl from config.shared.kdl + optional config.local.kdl.

    Returns a short 'shared' or 'shared + local' description when it generated,
    or None if zellij isn't installed (no dir) or the shared file is missing.
    """
    zellij_config = zellij_config_dir / 'config.kdl'
    zellij_shared = zellij_config_dir / 'config.shared.kdl'
    zellij_local = zellij_config_dir / 'config.local.kdl'

    if not (zellij_config_dir.exists() and zellij_shared.exists()):
        return None

    logger.debug("Generating zellij config.kdl from shared + local...")
    if not dry_run:
        content = zellij_shared.read_text()
        if zellij_local.exists():
            content += '\n// Machine-specific overrides from config.local.kdl\n'
            content += zellij_local.read_text()
        zellij_config.write_text(content)
    detail = "shared + local" if zellij_local.exists() else "shared"
    logger.success(f"Generated zellij/config.kdl from {detail}", indent=True)
    return detail


def install_brewfile(dotfiles_dir, args, logger):
    """Install Brewfile packages idempotently.

    Skips silently when brew is unavailable, the opt-out flag/env is set,
    or the Brewfile is already satisfied. Never runs `cleanup`, so packages
    present on the machine but absent from the Brewfile are left alone.
    """
    if args.skip_brew or os.environ.get('DOTFILES_SKIP_BREW'):
        logger.info("Skipping Brewfile (opt-out set)")
        return

    brewfile = dotfiles_dir / 'Brewfile'
    if not brewfile.exists():
        logger.debug("No Brewfile found, skipping")
        return

    if shutil.which('brew') is None:
        logger.info("brew not found on PATH, skipping Brewfile")
        return

    logger.header("Checking Brewfile...")
    check = subprocess.run(
        ['brew', 'bundle', 'check', f'--file={brewfile}'],
        capture_output=True, text=True,
    )
    if check.returncode == 0:
        logger.success("Brewfile dependencies already satisfied", indent=True)
        return

    if args.dry_run:
        logger.info(f"Would run: brew bundle install --file={brewfile}", indent=True)
        return

    logger.info("Installing missing Brewfile packages...", indent=True)
    install_cmd = ['brew', 'bundle', 'install', f'--file={brewfile}']
    if args.verbose:
        result = subprocess.run(install_cmd)
    else:
        result = subprocess.run(install_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            sys.stdout.write(result.stdout or '')
            sys.stderr.write(result.stderr or '')

    if result.returncode == 0:
        logger.success("Brewfile installed", indent=True)
    else:
        logger.error(f"brew bundle exited with status {result.returncode}", indent=True)


def main():
    """Main installation logic"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Install dotfiles via symlinks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./install.py                    # Install dotfiles
  ./install.py --dry-run          # Preview changes without executing
  ./install.py --verbose          # Show detailed output
  ./install.py --force            # Override without prompts
  ./install.py --dry-run --verbose # Combine flags
        """
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without executing')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed output')
    parser.add_argument('--force', action='store_true',
                        help='Override without prompts')
    parser.add_argument('--skip-brew', action='store_true',
                        help='Skip Brewfile install step (also: DOTFILES_SKIP_BREW=1)')

    args = parser.parse_args()

    # Initialize logger and state manager
    logger = Logger(verbose=args.verbose)
    state = StateManager()

    # Preserve existing installation records for items that are already installed
    state.installations = state.load()

    # Get dotfiles directory
    dotfiles_dir = get_dotfiles_dir()
    logger.debug(f"Dotfiles directory: {dotfiles_dir}")

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        print()

    # Pre-flight checks
    logger.debug("Running pre-flight checks...")

    # Ensure ~/.config exists
    config_dir = Path.home() / '.config'
    if not config_dir.exists():
        logger.info(f"Creating {config_dir}")
        if not args.dry_run:
            config_dir.mkdir(parents=True, exist_ok=True)

    # Counters for summary
    total = len(CONFIG_DIRS) + len(CONFIG_FILES)
    counters = {'installed': 0, 'skipped': 0, 'backed_up': 0, 'errors': 0}
    generated = []

    print()
    logger.info(f"Installing {total} items...")
    print()

    # Process directories and files
    for source_name, dest in CONFIG_DIRS.items():
        process_item(source_name, dest, 'dir', dotfiles_dir, state, args, logger, counters)

    for source_name, dest in CONFIG_FILES.items():
        process_item(source_name, dest, 'file', dotfiles_dir, state, args, logger, counters)

    # Special handling for SSH: ensure ~/.ssh permissions are correct
    fix_ssh_permissions(Path.home() / '.ssh', args.dry_run, logger)

    # Special handling for zellij: always regenerate config.kdl from shared + local
    zellij_detail = generate_zellij_config(
        Path.home() / '.config' / 'zellij', args.dry_run, logger
    )
    if zellij_detail:
        generated.append(f"zellij/config.kdl ({zellij_detail})")

    # Install Brewfile packages (idempotent, opt-out friendly)
    install_brewfile(dotfiles_dir, args, logger)

    # Save state file
    if not args.dry_run:
        logger.debug(f"Saving state to {state.state_file}")
        state.save()

    # Print summary
    print()
    print("=" * 60)
    logger.info("Installation Summary:")
    print(f"  Total items:     {total}")
    print(f"  Installed:       {counters['installed']}")
    print(f"  Skipped:         {counters['skipped']}")
    print(f"  Backed up:       {counters['backed_up']}")
    print(f"  Generated:       {len(generated)}")
    if generated:
        for item in generated:
            print(f"    - {item}")
    if counters['errors'] > 0:
        print(f"  Errors:          {counters['errors']}")
    print("=" * 60)

    if args.dry_run:
        print()
        logger.info("This was a DRY RUN - no changes were made")

    if counters['installed'] > 0 and not args.dry_run:
        print()
        logger.success("Installation complete!")
        print()
        logger.info("Next steps:")
        print("  - Restart your shell or run: exec $SHELL")
        print("  - Open nvim to initialize plugins (first run)")
        print("  - Auto-generated files (fish_variables, lazy-lock.json) will be created automatically")

    if counters['errors'] > 0:
        print()
        logger.error(f"Installation completed with {counters['errors']} error(s)")
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Installation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
