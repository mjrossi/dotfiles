#!/usr/bin/env python3
"""
Dotfiles uninstallation script - removes symlinks and restores backups.
"""

import argparse
import shutil
import sys
from pathlib import Path

# Import from lib.common
from lib.common import (
    CONFIG_DIRS, CONFIG_FILES, Logger, StateManager,
    get_dotfiles_dir, restore_backup, remove_symlink, is_managed_symlink, prompt_user
)


# Source-name → filename inside that source dir that must survive uninstall
PRESERVED_FILES = {
    'fish': 'config.local.fish',
    'zellij': 'config.kdl',
}


def find_preserved_file(source_name, item_type, dest, dotfiles_dir):
    """Locate the machine-specific file to preserve for a given source dir.

    Returns a {'source': Path, 'filename': str} dict, or None if there is
    nothing to preserve (unknown source, not a dir, or the file doesn't exist).
    """
    if item_type != 'dir' or not dest.is_symlink():
        return None

    filename = PRESERVED_FILES.get(source_name)
    if filename is None:
        return None

    local_config = dotfiles_dir / source_name / filename
    if not (local_config.exists() and local_config.is_file()):
        return None

    return {'source': local_config, 'filename': filename}


def preserve_file(file_to_preserve, dest, dry_run, logger):
    """Copy a preserved machine-specific file into the restored destination.

    Returns True when the file was preserved (or would be, in dry-run), False
    when the copy failed. Caller decides what to do with that (counter, etc.).
    """
    if dry_run:
        logger.info(f"Would preserve {file_to_preserve['filename']}", indent=True)
        return True

    target = dest / file_to_preserve['filename']
    try:
        # Ensure parent directory exists (in case no backup was restored)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_to_preserve['source'], target)
        logger.info(f"Preserved {file_to_preserve['filename']}", indent=True)
        return True
    except Exception as e:
        logger.warning(
            f"Could not preserve {file_to_preserve['filename']}: {e}", indent=True
        )
        return False


def main():
    """Main uninstallation logic"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Uninstall dotfiles symlinks and restore backups',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./uninstall.py                    # Uninstall dotfiles
  ./uninstall.py --dry-run          # Preview changes without executing
  ./uninstall.py --verbose          # Show detailed output
  ./uninstall.py --force            # Override without prompts
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
    state_mgr = StateManager()

    # Get dotfiles directory
    dotfiles_dir = get_dotfiles_dir()
    logger.debug(f"Dotfiles directory: {dotfiles_dir}")

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        print()

    # Load state
    logger.debug("Loading installation state...")
    installations = state_mgr.load()

    # Build list of symlinks to process
    to_remove = []

    if installations:
        logger.info(f"Found state file with {len(installations)} installed item(s)")
        for item in installations:
            dest = Path(item['destination'])
            to_remove.append({
                'type': item['type'],
                'source': item['source'],
                'dest': dest,
                'backup_created': item.get('backup_created', False)
            })
    else:
        logger.warning("No state file found, using configuration as fallback")
        logger.info("Will check all configured destinations for managed symlinks")

        # Use CONFIG_DIRS and CONFIG_FILES as fallback
        for source_name, dest in CONFIG_DIRS.items():
            to_remove.append({
                'type': 'dir',
                'source': source_name,
                'dest': dest,
                'backup_created': False  # Unknown
            })

        for source_name, dest in CONFIG_FILES.items():
            to_remove.append({
                'type': 'file',
                'source': source_name,
                'dest': dest,
                'backup_created': False  # Unknown
            })

    # Filter to only managed symlinks
    logger.debug("Filtering to managed symlinks...")
    managed = []
    for item in to_remove:
        dest = item['dest']
        if dest.exists() or dest.is_symlink():
            if is_managed_symlink(dest, dotfiles_dir):
                managed.append(item)
                logger.debug(f"Managed symlink: {dest}")
            else:
                logger.debug(f"Not a managed symlink: {dest}")

    if not managed:
        print()
        logger.info("No managed symlinks found to remove")
        print()
        logger.info("Nothing to do!")
        sys.exit(0)

    # Display what will be removed
    print()
    logger.info(f"Found {len(managed)} managed symlink(s) to remove:")
    print()
    for item in managed:
        backup_exists = Path(f"{item['dest']}.bak").exists()
        backup_info = " (backup exists)" if backup_exists else ""
        print(f"  - {item['source']} -> {item['dest']}{backup_info}")

    print()

    # Confirm with user
    if not args.force and not args.dry_run:
        if not prompt_user("Proceed with uninstallation?"):
            logger.info("Uninstallation cancelled")
            sys.exit(0)
        print()

    # Counters for summary
    removed = 0
    restored = 0
    errors = 0
    preserved = 0

    # Process each managed symlink
    for item in managed:
        dest = item['dest']
        source_name = item['source']

        logger.header(f"Uninstalling {source_name}...")

        logger.debug(f"Processing: {source_name}")
        logger.debug(f"  Destination: {dest}")

        # Check for machine-specific files to preserve before removal
        file_to_preserve = find_preserved_file(
            source_name, item['type'], dest, dotfiles_dir
        )
        if file_to_preserve:
            logger.debug(
                f"Found machine-specific file: {source_name}/{file_to_preserve['filename']}"
            )

        # Remove symlink
        if remove_symlink(dest, dotfiles_dir, dry_run=args.dry_run, logger=logger):
            logger.success("Removed symlink", indent=True)
            removed += 1

            # Try to restore backup
            if restore_backup(dest, dry_run=args.dry_run, logger=logger):
                logger.success("Restored backup", indent=True)
                restored += 1
            else:
                logger.debug(f"No backup found for {source_name}")

            # Preserve machine-specific file if found
            if file_to_preserve and preserve_file(
                file_to_preserve, dest, args.dry_run, logger
            ):
                preserved += 1
        else:
            logger.error("Failed to remove symlink", indent=True)
            errors += 1

    # Clean up state file
    if not args.dry_run and removed > 0:
        if prompt_user("Remove state file (.dotfiles-state)?", force=args.force):
            logger.debug("Removing state file")
            state_mgr.clear()
            logger.success("Removed state file")

    # Print summary
    print()
    print("=" * 60)
    logger.info("Uninstallation Summary:")
    print(f"  Symlinks removed:  {removed}")
    print(f"  Backups restored:  {restored}")
    if preserved > 0:
        print(f"  Local files preserved: {preserved}")
    if errors > 0:
        print(f"  Errors:            {errors}")
    print("=" * 60)

    if args.dry_run:
        print()
        logger.info("This was a DRY RUN - no changes were made")

    if removed > 0 and not args.dry_run:
        print()
        logger.success("Uninstallation complete!")

        # Check for remaining .bak files
        remaining_backups = []
        for item in managed:
            backup = Path(f"{item['dest']}.bak")
            if backup.exists():
                remaining_backups.append(backup)

        if remaining_backups:
            print()
            logger.info("Remaining backup files (not restored):")
            for backup in remaining_backups:
                print(f"  - {backup}")
            print()
            logger.info("You can manually restore or delete these files")

    if errors > 0:
        print()
        logger.error(f"Uninstallation completed with {errors} error(s)")
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Uninstallation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
