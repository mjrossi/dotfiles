#!/usr/bin/env python3
"""
Dotfiles uninstallation script - removes symlinks and restores backups.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

# Import from lib.common
from lib.common import (
    CONFIG_DIRS, CONFIG_FILES, Logger, StateManager,
    build_arg_parser, get_dotfiles_dir, discover_backup,
    restore_backup_at, remove_symlink,
    is_managed_symlink, prompt_user, run_main,
)


# Source-name → filename inside that source dir that must survive uninstall
PRESERVED_FILES = {
    'fish': 'config.local.fish',
    'zellij': 'config.kdl',
}


def find_preserved_file(
    source_name: str, item_type: str, dest: Path, dotfiles_dir: Path
) -> dict[str, Any] | None:
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


def preserve_file(
    file_to_preserve: dict[str, Any], dest: Path, dry_run: bool, logger: Logger
) -> bool:
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


def owned_backup(item: dict[str, Any]) -> Path | None:
    """Path of the backup this installation record owns, or None.

    StateManager.load() upgrades 1.0 records by recording the discovered
    backup path, so a record normally names its exact file. The discovery
    fallback remains for a 1.0 record whose backup could not be found at load
    time. A missing state file, or a record that says no backup was created,
    never claims a similarly named file that may belong to the user.

    Used for the removal preview and the leftover report as well as the
    restore itself, so all three agree on which file is ours.
    """
    recorded_path = item.get('backup_path')
    if recorded_path:
        return Path(recorded_path)
    if item.get('backup_created') is True:
        return discover_backup(Path(item['destination']))
    return None


def restore_item_backup(item: dict[str, Any], dry_run: bool, logger: Logger) -> bool:
    """Restore only the backup associated with this installation record."""
    backup = owned_backup(item)
    if backup is None:
        return False
    if not backup.exists():
        # Distinct from "this record never had a backup": the file we
        # recorded has been moved or deleted since install, and the user
        # is the only one who can say where it went.
        logger.warning(
            f"Recorded backup is missing, not restored: {backup}", indent=True
        )
        return False
    return restore_backup_at(
        Path(item['destination']), backup, dry_run=dry_run, logger=logger
    )


def load_records(state_mgr: StateManager, logger: Logger) -> list[dict[str, Any]]:
    """Installation records to consider: the state file's, or every configured item.

    Without a state file the configured destinations stand in, shaped like
    state records but with backup_created None: unknown, so no backup is
    guessed at.
    """
    logger.debug("Loading installation state...")
    installations = state_mgr.load(logger)
    if installations:
        logger.info(f"Found state file with {len(installations)} installed item(s)")
        return installations

    logger.warning("No state file found, using configuration as fallback")
    logger.info("Will check all configured destinations for managed symlinks")
    records = []
    for item_type, mapping in (('dir', CONFIG_DIRS), ('file', CONFIG_FILES)):
        for source_name, dest in mapping.items():
            records.append({
                'type': item_type,
                'source': source_name,
                'destination': str(dest),
                'backup_created': None,  # Unknown; do not guess which backup belongs to us
                'backup_path': None,
            })
    return records


def filter_managed(
    records: list[dict[str, Any]], dotfiles_dir: Path, logger: Logger
) -> list[dict[str, Any]]:
    """Keep only records whose destination is a symlink into this repo."""
    logger.debug("Filtering to managed symlinks...")
    managed = []
    for item in records:
        dest = Path(item['destination'])
        if dest.exists() or dest.is_symlink():
            if is_managed_symlink(dest, dotfiles_dir):
                managed.append(item)
                logger.debug(f"Managed symlink: {dest}")
            else:
                logger.debug(f"Not a managed symlink: {dest}")
    return managed


def confirm_removal(
    managed: list[dict[str, Any]], args: argparse.Namespace, logger: Logger
) -> bool:
    """Show what will be removed and ask to proceed (skipped by --force/--dry-run)."""
    print()
    logger.info(f"Found {len(managed)} managed symlink(s) to remove:")
    print()
    for item in managed:
        backup = owned_backup(item)
        backup_info = " (backup exists)" if backup and backup.exists() else ""
        print(f"  - {item['source']} -> {item['destination']}{backup_info}")

    print()

    if not args.force and not args.dry_run:
        if not prompt_user("Proceed with uninstallation?"):
            return False
        print()
    return True


def remove_items(
    managed: list[dict[str, Any]],
    dotfiles_dir: Path,
    args: argparse.Namespace,
    logger: Logger,
) -> dict[str, int]:
    """Remove each managed symlink, restore its backup, keep local files."""
    counters = {'removed': 0, 'restored': 0, 'errors': 0, 'preserved': 0}

    for item in managed:
        dest = Path(item['destination'])
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
            counters['removed'] += 1

            # Try to restore backup
            if restore_item_backup(item, dry_run=args.dry_run, logger=logger):
                logger.success("Restored backup", indent=True)
                counters['restored'] += 1
            else:
                logger.debug(f"No backup found for {source_name}")

            # Preserve machine-specific file if found
            if file_to_preserve and preserve_file(
                file_to_preserve, dest, args.dry_run, logger
            ):
                counters['preserved'] += 1
        else:
            logger.error("Failed to remove symlink", indent=True)
            counters['errors'] += 1

    return counters


def summarise(
    managed: list[dict[str, Any]],
    counters: dict[str, int],
    args: argparse.Namespace,
    logger: Logger,
) -> None:
    """Print the summary and any backups that were left in place."""
    print()
    print("=" * 60)
    logger.info("Uninstallation Summary:")
    print(f"  Symlinks removed:  {counters['removed']}")
    print(f"  Backups restored:  {counters['restored']}")
    if counters['preserved'] > 0:
        print(f"  Local files preserved: {counters['preserved']}")
    if counters['errors'] > 0:
        print(f"  Errors:            {counters['errors']}")
    print("=" * 60)

    if args.dry_run:
        print()
        logger.info("This was a DRY RUN - no changes were made")

    if counters['removed'] > 0 and not args.dry_run:
        print()
        logger.success("Uninstallation complete!")

        # Check for remaining .bak files
        remaining_backups = []
        for item in managed:
            backup = owned_backup(item)
            if backup and backup.exists():
                remaining_backups.append(backup)

        if remaining_backups:
            print()
            logger.info("Remaining backup files (not restored):")
            for backup in remaining_backups:
                print(f"  - {backup}")
            print()
            logger.info("You can manually restore or delete these files")


def main() -> None:
    """Main uninstallation logic"""
    parser = build_arg_parser(
        description='Uninstall dotfiles symlinks and restore backups',
        epilog="""
Examples:
  ./uninstall.py                    # Uninstall dotfiles
  ./uninstall.py --dry-run          # Preview changes without executing
  ./uninstall.py --verbose          # Show detailed output
  ./uninstall.py --force            # Override without prompts
        """,
    )
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

    records = load_records(state_mgr, logger)
    managed = filter_managed(records, dotfiles_dir, logger)

    if not managed:
        print()
        logger.info("No managed symlinks found to remove")
        print()
        logger.info("Nothing to do!")
        sys.exit(0)

    if not confirm_removal(managed, args, logger):
        logger.info("Uninstallation cancelled")
        sys.exit(0)

    counters = remove_items(managed, dotfiles_dir, args, logger)

    # Clean up state file
    if not args.dry_run and counters['removed'] > 0:
        if prompt_user("Remove state file (.dotfiles-state)?", force=args.force):
            logger.debug("Removing state file")
            state_mgr.clear()
            logger.success("Removed state file")

    summarise(managed, counters, args, logger)

    if counters['errors'] > 0:
        print()
        logger.error(f"Uninstallation completed with {counters['errors']} error(s)")
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    run_main(main, 'Uninstallation')
