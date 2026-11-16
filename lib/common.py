#!/usr/bin/env python3
"""
Shared functions and configuration for dotfiles management scripts.
Requires: Python 3.9+ (matches CI test matrix)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable
import os
import shutil
import sys
import json
from datetime import datetime


# Configuration: Directory mappings
CONFIG_DIRS: dict[str, Path] = {
    'fish': Path.home() / '.config' / 'fish',
    'nvim': Path.home() / '.config' / 'nvim',
    'zellij': Path.home() / '.config' / 'zellij',
    'mise': Path.home() / '.config' / 'mise',
    'ghostty': Path.home() / '.config' / 'ghostty',
}

# Claude Code skills vendored under claude/skills/. Each one is linked on its
# own rather than linking ~/.claude/skills as a whole: that directory also
# holds skills this repo does not own (account-synced ones under synced/,
# standalone git clones), so it has to stay a real directory.
CLAUDE_SKILLS: tuple[str, ...] = (
    'ai-generated-code-review',
    'anti-patterns-catalog',
    'concurrency-patterns',
    'detect-code-smells',
    'error-handling-patterns',
    'go-review-patterns',
    'performance-anti-patterns',
    'refactor',
    'refactor-composing-methods',
    'refactor-moving-features',
    'refactor-organizing-data',
    'refactor-simplifying-method-calls',
    'refactoring-decision-matrix',
    'review-accuracy-calibration',
    'security-patterns-code-review',
    'typescript-review-patterns',
)
CONFIG_DIRS.update({
    f'claude/skills/{name}': Path.home() / '.claude' / 'skills' / name
    for name in CLAUDE_SKILLS
})

# Configuration: File mappings
CONFIG_FILES: dict[str, Path] = {
    'gitconfig': Path.home() / '.gitconfig',
    'gitignore_global': Path.home() / '.gitignore_global',
    'ssh/config': Path.home() / '.ssh' / 'config',
}



def get_dotfiles_dir() -> Path:
    """Get absolute path to dotfiles directory"""
    # Assumes this file is in lib/common.py, so dotfiles dir is parent.parent
    return Path(__file__).parent.parent.resolve()


# State file location. Override via DOTFILES_STATE_FILE for isolated test
# runs (CI smoke test, local sandbox) so a scratch HOME doesn't share state
# with the user's real installation.
STATE_FILE = get_dotfiles_dir() / '.dotfiles-state'


class Logger:
    """Handles colored logging output"""

    _BLUE = '\033[94m'
    _GREEN = '\033[92m'
    _YELLOW = '\033[93m'
    _RED = '\033[91m'
    _GRAY = '\033[90m'
    _RESET = '\033[0m'

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.use_color_stdout = sys.stdout.isatty()
        self.use_color_stderr = sys.stderr.isatty()

    def _c(self, code: str, stream: str = "stdout") -> str:
        """Return color code only when writing to a TTY."""
        use_color = self.use_color_stderr if stream == "stderr" else self.use_color_stdout
        return code if use_color else ""

    def header(self, msg: str) -> None:
        """Print section header without prefix"""
        print(f"\n{msg}")

    def info(self, msg: str, indent: bool = False) -> None:
        """Print informational message in blue"""
        prefix = "  " if indent else ""
        print(f"{prefix}{self._c(self._BLUE)}ℹ{self._c(self._RESET)} {msg}")

    def success(self, msg: str, indent: bool = False) -> None:
        """Print success message in green"""
        prefix = "  " if indent else ""
        print(f"{prefix}{self._c(self._GREEN)}✓{self._c(self._RESET)} {msg}")

    def warning(self, msg: str, indent: bool = False) -> None:
        """Print warning message in yellow"""
        prefix = "  " if indent else ""
        print(f"{prefix}{self._c(self._YELLOW)}⚠{self._c(self._RESET)} {msg}")

    def error(self, msg: str, indent: bool = False) -> None:
        """Print error message in red"""
        prefix = "  " if indent else ""
        print(f"{prefix}{self._c(self._RED, 'stderr')}✗{self._c(self._RESET, 'stderr')} {msg}", file=sys.stderr)

    def debug(self, msg: str) -> None:
        """Print debug message in gray (only shown in verbose mode)"""
        if self.verbose:
            print(f"{self._c(self._GRAY)}[DEBUG]{self._c(self._RESET)} {msg}")


class StateManager:
    """Manages the .dotfiles-state file for tracking installations"""

    def __init__(self, state_file: Path | None = None):
        # Precedence: explicit arg > DOTFILES_STATE_FILE env override > repo default.
        # The env override lets the CI smoke test (and local sandboxes) keep a
        # scratch HOME from stomping on the user's real state file.
        if state_file is not None:
            self.state_file = state_file
        elif env_override := os.environ.get('DOTFILES_STATE_FILE'):
            self.state_file = Path(env_override)
        else:
            self.state_file = STATE_FILE
        self.installations: list[dict[str, Any]] = []

    def add(
        self,
        item_type: str,
        source: str,
        dest: Path,
        backup_created: bool,
        backup_path: Path | None = None,
    ) -> None:
        """Add (or replace) an installation record, keyed by destination."""
        record = {
            'type': item_type,
            'source': source,
            'destination': str(dest),
            'backup_created': backup_created,
            'backup_path': str(backup_path) if backup_path is not None else None,
            'timestamp': datetime.now().isoformat(),
        }
        for i, existing in enumerate(self.installations):
            if existing['destination'] == record['destination']:
                # A reinstall that takes no new backup -- relinking a managed
                # symlink whose source moved, or replacing a broken one --
                # must not erase the backup the first install recorded. That
                # file is still the user's pre-dotfiles content, and uninstall
                # needs its exact path to put it back.
                if backup_path is None and not backup_created:
                    if existing.get('backup_path'):
                        record['backup_path'] = existing['backup_path']
                        record['backup_created'] = True
                    elif existing.get('backup_created') is True:
                        record['backup_created'] = True
                self.installations[i] = record
                return
        self.installations.append(record)

    def save(self) -> None:
        """Save state to JSON file.

        Writes atomically: dump to a sibling temp file, then os.replace onto
        the real path so a crash mid-write cannot leave a truncated JSON file.
        """
        state = {'version': '1.1', 'installed': self.installations}
        tmp = self.state_file.with_suffix(self.state_file.suffix + '.tmp')
        with open(tmp, 'w') as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, self.state_file)

    def load(self, logger: Logger | None = None) -> list[dict[str, Any]]:
        """Load state from the JSON file into self.installations and return it.

        Records written by version 1.0 know only that a backup was taken, not
        what it was called. They are upgraded here, once, by resolving the
        backup filename with discover_backup() and recording it, so that a
        file saved afterwards as 1.1 never holds 1.0-shaped records and
        nothing downstream needs a second, legacy code path.
        """
        self.installations = []
        if not self.state_file.exists():
            return self.installations

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
        except json.JSONDecodeError as e:
            msg = f"Could not parse state file: {e}"
            if logger:
                logger.warning(msg)
            else:
                print(f"Warning: {msg}", file=sys.stderr)
            return self.installations

        self.installations = [
            self._migrate_record(record) for record in state.get('installed', [])
        ]
        return self.installations

    @staticmethod
    def _migrate_record(record: dict[str, Any]) -> dict[str, Any]:
        """Upgrade a 1.0 record (no backup_path key) to the 1.1 shape."""
        if 'backup_path' in record:
            return record
        backup = None
        if record.get('backup_created') is True:
            backup = discover_backup(Path(record['destination']))
        return {**record, 'backup_path': str(backup) if backup is not None else None}

    def prune(self, configured_sources: set[str], dotfiles_dir: Path) -> list[dict[str, Any]]:
        """Drop records for sources that are no longer configured.

        Only records that uninstall could no longer act on are dropped: if the
        destination is still a symlink into this repo, the record is kept, so
        uninstall can still remove that link and restore its backup. Returns
        the records that were kept despite their source being gone.
        """
        kept, orphaned = [], []
        for record in self.installations:
            if record['source'] in configured_sources:
                kept.append(record)
            elif is_managed_symlink(Path(record['destination']), dotfiles_dir):
                kept.append(record)
                orphaned.append(record)
        self.installations = kept
        return orphaned

    def clear(self) -> None:
        """Remove state file"""
        if self.state_file.exists():
            self.state_file.unlink()


def backup_path(path: Path, dry_run: bool = False, logger: Logger | None = None) -> Path | None:
    """
    Rename path to path.bak (handle conflicts with .bak.1, .bak.2, etc.)

    Args:
        path: Path to backup
        dry_run: If True, don't actually move files
        logger: Optional logger for debug output

    Returns:
        Path to backup location, or None if backup wasn't needed
    """
    if not path.exists():
        return None

    # Find available backup name
    backup = Path(f"{path}.bak")
    counter = 1
    while backup.exists():
        backup = Path(f"{path}.bak.{counter}")
        counter += 1

    if logger:
        logger.debug(f"Backing up {path} -> {backup}")

    if not dry_run:
        shutil.move(path, backup)

    return backup


def discover_backup(path: Path) -> Path | None:
    """
    Find the newest backup of `path`, or None.

    Only for legacy 1.0 state records, which know that a backup was taken but
    not what it was named, so the name has to be guessed back: the
    highest-numbered `.bak.N` is the newest. StateManager.load() calls this
    once to upgrade such records; records written by this version carry the
    exact path instead -- see `restore_backup_at`.
    """
    counter = 1
    while Path(f"{path}.bak.{counter}").exists():
        counter += 1

    if counter > 1:
        return Path(f"{path}.bak.{counter - 1}")
    if Path(f"{path}.bak").exists():
        return Path(f"{path}.bak")
    return None


def restore_backup_at(
    path: Path,
    backup: Path,
    dry_run: bool = False,
    logger: Logger | None = None,
) -> bool:
    """Restore one exact backup path recorded during installation."""
    if not backup.exists():
        return False

    if logger:
        logger.debug(f"Restoring recorded backup {backup} -> {path}")

    if not dry_run:
        shutil.move(backup, path)

    return True


def create_symlink(source: Path, dest: Path, dry_run: bool = False, logger: Logger | None = None) -> bool:
    """
    Create symlink with validation

    Args:
        source: Source path (must exist)
        dest: Destination path for symlink
        dry_run: If True, don't actually create symlink
        logger: Optional logger for debug output

    Returns:
        True if symlink was created successfully, False otherwise
    """
    # Validate source exists
    if not source.exists():
        if logger:
            logger.error(f"Source does not exist: {source}")
        return False

    if logger:
        logger.debug(f"Creating symlink: {dest} -> {source}")

    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            dest.symlink_to(source)
        except OSError as e:
            if logger:
                logger.error(f"Failed to create symlink: {e}")
            return False

    return True


def remove_symlink(dest: Path, dotfiles_dir: Path, dry_run: bool = False, logger: Logger | None = None) -> bool:
    """
    Remove symlink only if managed by us

    Args:
        dest: Destination path (should be a symlink)
        dotfiles_dir: Path to dotfiles directory
        dry_run: If True, don't actually remove symlink
        logger: Optional logger for debug output

    Returns:
        True if symlink was removed, False otherwise
    """
    if not dest.is_symlink():
        if logger:
            logger.error(f"Not a symlink, refusing to remove: {dest}")
        return False

    if not is_managed_symlink(dest, dotfiles_dir):
        if logger:
            logger.error(f"Symlink not managed by us, refusing to remove: {dest}")
        return False

    if logger:
        logger.debug(f"Removing symlink: {dest}")

    if not dry_run:
        try:
            dest.unlink()
        except OSError as e:
            if logger:
                logger.error(f"Failed to remove symlink: {e}")
            return False

    return True


def symlink_target(path: Path) -> Path:
    """Absolute, normalised path that the symlink `path` points at.

    Relative link text is taken relative to the link's own directory, and the
    result is resolved, so absolute link text containing ``..`` segments (or
    passing through other symlinks) is normalised too. Raises OSError if
    `path` is not a symlink.
    """
    target = path.readlink()
    if not target.is_absolute():
        target = path.parent / target
    return target.resolve()


def is_managed_symlink(path: Path, dotfiles_dir: Path) -> bool:
    """
    Check if symlink points to our dotfiles

    Args:
        path: Path to check
        dotfiles_dir: Path to dotfiles directory

    Returns:
        True if path is a symlink pointing to dotfiles_dir
    """
    if not path.is_symlink():
        return False

    try:
        # symlink_target normalises absolute and relative link text alike;
        # absolute text can still contain ``..`` segments that escape the
        # repository.
        target = symlink_target(path)
        dotfiles_dir = dotfiles_dir.resolve()

        # is_relative_to avoids the prefix-match pitfall of str.startswith,
        # e.g. /home/me/dotfiles-old is NOT under /home/me/dotfiles.
        try:
            return target.is_relative_to(dotfiles_dir)
        except ValueError:
            return False
    except OSError:
        return False


def prompt_user(question: str, force: bool = False) -> bool:
    """
    Ask yes/no questions (respects --force flag)

    Args:
        question: Question to ask user
        force: If True, automatically return True without prompting

    Returns:
        True if user answered yes (or force=True), False otherwise
    """
    if force:
        return True

    while True:
        response = input(f"{question} [y/n]: ").lower().strip()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print("Please answer 'y' or 'n'")


def build_arg_parser(
    description: str, epilog: str, include_skip_brew: bool = False
) -> argparse.ArgumentParser:
    """Shared argparse skeleton for install.py and uninstall.py."""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without executing')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed output')
    # install.py never prompts, so --force only does something for
    # uninstall.py. It stays on both so scripts can pass it either way.
    parser.add_argument('--force', action='store_true',
                        help='Skip confirmation prompts (uninstall only; '
                             'install never prompts)')
    if include_skip_brew:
        parser.add_argument('--skip-brew', action='store_true',
                            help='Skip Brewfile install step (also: DOTFILES_SKIP_BREW=1)')
    return parser


def run_main(main_fn: Callable[[], None], action_name: str) -> None:
    """Invoke main_fn, handling Ctrl-C cleanly. Other exceptions propagate
    so Python's default traceback does the reporting."""
    try:
        main_fn()
    except KeyboardInterrupt:
        print()
        print(f"{action_name} interrupted by user")
        sys.exit(130)
