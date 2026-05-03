#!/usr/bin/env python3
"""
Shared functions and configuration for dotfiles management scripts.
Requires: Python 3.10+ (matches CI test matrix)
"""

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

# Configuration: File mappings
CONFIG_FILES: dict[str, Path] = {
    'gitconfig': Path.home() / '.gitconfig',
    'gitignore_global': Path.home() / '.gitignore_global',
    'ssh/config': Path.home() / '.ssh' / 'config',
    'launchd/com.proton.pass-cli.ssh-agent.plist':
        Path.home() / 'Library' / 'LaunchAgents' / 'com.proton.pass-cli.ssh-agent.plist',
}

# State file location. Override via DOTFILES_STATE_FILE for isolated test
# runs (CI smoke test, local sandbox) so a scratch HOME doesn't share state
# with the user's real installation.
STATE_FILE = Path(__file__).parent.parent / '.dotfiles-state'


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

    def add(self, item_type: str, source: str, dest: Path, backup_created: bool) -> None:
        """Add (or replace) an installation record, keyed by destination."""
        record = {
            'type': item_type,
            'source': source,
            'destination': str(dest),
            'backup_created': backup_created,
            'timestamp': datetime.now().isoformat(),
        }
        for i, existing in enumerate(self.installations):
            if existing['destination'] == record['destination']:
                self.installations[i] = record
                return
        self.installations.append(record)

    def save(self) -> None:
        """Save state to JSON file.

        Writes atomically: dump to a sibling temp file, then os.replace onto
        the real path so a crash mid-write cannot leave a truncated JSON file.
        """
        state = {'version': '1.0', 'installed': self.installations}
        tmp = self.state_file.with_suffix(self.state_file.suffix + '.tmp')
        with open(tmp, 'w') as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, self.state_file)

    def load(self) -> list[dict[str, Any]]:
        """Load state from JSON file"""
        if not self.state_file.exists():
            return []

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                return state.get('installed', [])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse state file: {e}", file=sys.stderr)
            return []

    def clear(self) -> None:
        """Remove state file"""
        if self.state_file.exists():
            self.state_file.unlink()


def get_dotfiles_dir() -> Path:
    """Get absolute path to dotfiles directory"""
    # Assumes this file is in lib/common.py, so dotfiles dir is parent.parent
    return Path(__file__).parent.parent.resolve()


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


def restore_backup(path: Path, dry_run: bool = False, logger: Logger | None = None) -> bool:
    """
    Rename path.bak back to path

    Args:
        path: Path to restore (will look for path.bak)
        dry_run: If True, don't actually move files
        logger: Optional logger for debug output

    Returns:
        True if backup was restored, False otherwise
    """
    # Find the highest-numbered backup first (newest)
    counter = 1
    while Path(f"{path}.bak.{counter}").exists():
        counter += 1

    if counter > 1:
        backup = Path(f"{path}.bak.{counter - 1}")
    elif Path(f"{path}.bak").exists():
        backup = Path(f"{path}.bak")
    else:
        return False

    if logger:
        logger.debug(f"Restoring backup {backup} -> {path}")

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
        target = path.readlink()
        # Handle both absolute and relative paths
        if not target.is_absolute():
            target = (path.parent / target).resolve()

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
    parser.add_argument('--force', action='store_true',
                        help='Override without prompts')
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
