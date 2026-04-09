#!/usr/bin/env python3
"""
Dotfiles installation script - creates symlinks for configuration files and directories.
"""

import argparse
import sys
from pathlib import Path

# Import from lib.common
from lib.common import (
    CONFIG_DIRS, CONFIG_FILES, Logger, StateManager,
    get_dotfiles_dir, backup_path, create_symlink, is_managed_symlink
)


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
    installed = 0
    skipped = 0
    backed_up = 0
    errors = 0

    print()
    logger.info(f"Installing {total} items...")
    print()

    # Process directories
    for source_name, dest in CONFIG_DIRS.items():
        source = dotfiles_dir / source_name

        logger.header(f"Installing {source_name}...")

        logger.debug(f"Processing directory: {source_name}")
        logger.debug(f"  Source: {source}")
        logger.debug(f"  Destination: {dest}")

        # Validate source exists
        if not source.exists():
            logger.error(f"Source directory does not exist: {source}", indent=True)
            errors += 1
            continue

        if not source.is_dir():
            logger.error(f"Source is not a directory: {source}", indent=True)
            errors += 1
            continue

        # Track if this specific item had a backup created
        had_backup = False

        # Check destination status
        if dest.exists() or dest.is_symlink():
            # Check if it's already a symlink to our dotfiles
            if dest.is_symlink() and is_managed_symlink(dest, dotfiles_dir):
                target = dest.readlink()
                if not target.is_absolute():
                    target = (dest.parent / target).resolve()

                if target == source:
                    logger.debug(f"Already installed: {source_name}")
                    logger.info(f"Skipped (already installed)", indent=True)
                    skipped += 1
                    continue
                else:
                    logger.warning(f"Symlink exists but points to different location: {dest} -> {target}", indent=True)

            # Check if it's a directory or file
            if dest.exists() and dest.is_dir() and not dest.is_symlink():
                # It's a real directory, need to back it up
                backup = backup_path(dest, dry_run=args.dry_run, logger=logger)
                had_backup = bool(backup)
                if backup:
                    backed_up += 1
                    logger.success(f"Backed up existing directory", indent=True)

            elif dest.exists() and dest.is_file():
                logger.error(f"Destination is a file, cannot replace with directory", indent=True)
                errors += 1
                continue

            elif dest.is_symlink() and not dest.exists():
                # Broken symlink
                logger.warning(f"Removing broken symlink", indent=True)
                if not args.dry_run:
                    dest.unlink()

        # Create symlink
        logger.debug(f"Creating symlink: {dest} -> {source}")

        if create_symlink(source, dest, dry_run=args.dry_run, logger=logger):
            logger.success(f"Created symlink", indent=True)
            installed += 1

            # Save to state
            if not args.dry_run:
                state.add('dir', source_name, dest, backup_created=had_backup)
        else:
            errors += 1

    # Process files
    for source_name, dest in CONFIG_FILES.items():
        source = dotfiles_dir / source_name

        logger.header(f"Installing {source_name}...")

        logger.debug(f"Processing file: {source_name}")
        logger.debug(f"  Source: {source}")
        logger.debug(f"  Destination: {dest}")

        # Validate source exists
        if not source.exists():
            logger.error(f"Source file does not exist: {source}", indent=True)
            errors += 1
            continue

        if not source.is_file():
            logger.error(f"Source is not a file: {source}", indent=True)
            errors += 1
            continue

        # Track if this specific item had a backup created
        had_backup = False

        # Check destination status
        if dest.exists() or dest.is_symlink():
            # Check if it's already a symlink to our dotfiles
            if dest.is_symlink() and is_managed_symlink(dest, dotfiles_dir):
                target = dest.readlink()
                if not target.is_absolute():
                    target = (dest.parent / target).resolve()

                if target == source:
                    logger.debug(f"Already installed: {source_name}")
                    logger.info(f"Skipped (already installed)", indent=True)
                    skipped += 1
                    continue

            # Check if it's a file or directory
            if dest.exists() and dest.is_file() and not dest.is_symlink():
                # It's a real file, need to back it up
                backup = backup_path(dest, dry_run=args.dry_run, logger=logger)
                had_backup = bool(backup)
                if backup:
                    backed_up += 1
                    logger.success(f"Backed up existing file", indent=True)

            elif dest.is_symlink() and not dest.exists():
                # Broken symlink
                logger.warning(f"Removing broken symlink", indent=True)
                if not args.dry_run:
                    dest.unlink()

        # Create symlink
        logger.debug(f"Creating symlink: {dest} -> {source}")

        if create_symlink(source, dest, dry_run=args.dry_run, logger=logger):
            logger.success(f"Created symlink", indent=True)
            installed += 1

            # Save to state
            if not args.dry_run:
                state.add('file', source_name, dest, backup_created=had_backup)
        else:
            errors += 1

    # Special handling for SSH: ensure ~/.ssh permissions are correct
    ssh_dir = Path.home() / '.ssh'
    if ssh_dir.exists():
        import os
        current_perms = oct(ssh_dir.stat().st_mode)[-3:]
        if current_perms != '700':
            logger.debug(f"Fixing ~/.ssh permissions: {current_perms} -> 700")
            if not args.dry_run:
                os.chmod(str(ssh_dir), 0o700)
            logger.success("Set ~/.ssh directory permissions to 700", indent=True)

        ssh_config = ssh_dir / 'config'
        if ssh_config.exists() or ssh_config.is_symlink():
            config_perms = oct(os.stat(str(ssh_config)).st_mode)[-3:]
            if config_perms != '600':
                logger.debug(f"Fixing ~/.ssh/config permissions: {config_perms} -> 600")
                if not args.dry_run:
                    os.chmod(str(ssh_config), 0o600)
                logger.success("Set ~/.ssh/config permissions to 600", indent=True)

    # Special handling for zellij: copy config.shared.kdl to config.kdl if needed
    zellij_config_dir = Path.home() / '.config' / 'zellij'
    zellij_config = zellij_config_dir / 'config.kdl'
    zellij_shared = zellij_config_dir / 'config.shared.kdl'

    if zellij_config_dir.exists() and zellij_shared.exists():
        # Only process if config.kdl doesn't exist yet
        if not zellij_config.exists():
            logger.debug("Processing zellij config setup...")
            logger.success("Created config.kdl from config.shared.kdl", indent=True)
            if not args.dry_run:
                import shutil
                shutil.copy2(str(zellij_shared), str(zellij_config))

    # Save state file
    if not args.dry_run and installed > 0:
        logger.debug(f"Saving state to {state.state_file}")
        state.save()

    # Print summary
    print()
    print("=" * 60)
    logger.info("Installation Summary:")
    print(f"  Total items:     {total}")
    print(f"  Installed:       {installed}")
    print(f"  Skipped:         {skipped}")
    print(f"  Backed up:       {backed_up}")
    if errors > 0:
        print(f"  Errors:          {errors}")
    print("=" * 60)

    if args.dry_run:
        print()
        logger.info("This was a DRY RUN - no changes were made")

    if installed > 0 and not args.dry_run:
        print()
        logger.success("Installation complete!")
        print()
        logger.info("Next steps:")
        print("  - Restart your shell or run: exec $SHELL")
        print("  - Open nvim to initialize plugins (first run)")
        print("  - Auto-generated files (fish_variables, lazy-lock.json) will be created automatically")

    if errors > 0:
        print()
        logger.error(f"Installation completed with {errors} error(s)")
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
