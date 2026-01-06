#!/usr/bin/env python3
"""
Shared functions and configuration for dotfiles management scripts.
Requires: Python 3.6+ (for f-strings and pathlib)
"""

from pathlib import Path
from typing import Dict, List, Optional
import shutil
import sys
import json
from datetime import datetime


# Configuration: Directory mappings
CONFIG_DIRS: Dict[str, Path] = {
    'fish': Path.home() / '.config' / 'fish',
    'nvim': Path.home() / '.config' / 'nvim',
    'zellij': Path.home() / '.config' / 'zellij',
    'mise': Path.home() / '.config' / 'mise',
}

# Configuration: File mappings
CONFIG_FILES: Dict[str, Path] = {
    'gitconfig': Path.home() / '.gitconfig',
    'gitignore_global': Path.home() / '.gitignore_global',
}

# Files/patterns to never symlink
IGNORE_PATTERNS: List[str] = [
    'Rakefile', 'README.md', '.DS_Store', '.git', '.gitignore',
    '*.bak', 'install.py', 'uninstall.py', 'lib', '.dotfiles-state',
    '*.template', 'config.local.fish', 'tests', 'run_tests.sh',
]

# State file location
STATE_FILE = Path(__file__).parent.parent / '.dotfiles-state'


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class Logger:
    """Handles colored logging output"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def header(self, msg: str) -> None:
        """Print section header without prefix"""
        print(f"\n{msg}")

    def info(self, msg: str, indent: bool = False) -> None:
        """Print informational message in blue"""
        prefix = "  " if indent else ""
        print(f"{prefix}{Colors.BLUE}ℹ{Colors.RESET} {msg}")

    def success(self, msg: str, indent: bool = False) -> None:
        """Print success message in green"""
        prefix = "  " if indent else ""
        print(f"{prefix}{Colors.GREEN}✓{Colors.RESET} {msg}")

    def warning(self, msg: str, indent: bool = False) -> None:
        """Print warning message in yellow"""
        prefix = "  " if indent else ""
        print(f"{prefix}{Colors.YELLOW}⚠{Colors.RESET} {msg}")

    def error(self, msg: str, indent: bool = False) -> None:
        """Print error message in red"""
        prefix = "  " if indent else ""
        print(f"{prefix}{Colors.RED}✗{Colors.RESET} {msg}", file=sys.stderr)

    def debug(self, msg: str) -> None:
        """Print debug message in gray (only shown in verbose mode)"""
        if self.verbose:
            print(f"{Colors.GRAY}[DEBUG]{Colors.RESET} {msg}")


class StateManager:
    """Manages the .dotfiles-state file for tracking installations"""

    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self.installations: List[Dict[str, any]] = []

    def add(self, type: str, source: str, dest: Path, backup_created: bool) -> None:
        """Add an installation record"""
        self.installations.append({
            'type': type,
            'source': source,
            'destination': str(dest),
            'backup_created': backup_created,
            'timestamp': datetime.now().isoformat()
        })

    def save(self) -> None:
        """Save state to JSON file"""
        state = {
            'version': '1.0',
            'installed': self.installations
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def load(self) -> List[Dict[str, any]]:
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


def backup_path(path: Path, dry_run: bool = False, logger: Optional[Logger] = None) -> Optional[Path]:
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
        shutil.move(str(path), str(backup))

    return backup


def restore_backup(path: Path, dry_run: bool = False, logger: Optional[Logger] = None) -> bool:
    """
    Rename path.bak back to path

    Args:
        path: Path to restore (will look for path.bak)
        dry_run: If True, don't actually move files
        logger: Optional logger for debug output

    Returns:
        True if backup was restored, False otherwise
    """
    backup = Path(f"{path}.bak")

    if not backup.exists():
        # Try numbered backups
        backup = Path(f"{path}.bak.1")
        if not backup.exists():
            return False

    if logger:
        logger.debug(f"Restoring backup {backup} -> {path}")

    if not dry_run:
        shutil.move(str(backup), str(path))

    return True


def create_symlink(source: Path, dest: Path, dry_run: bool = False, logger: Optional[Logger] = None) -> bool:
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

    # Ensure parent directory exists
    dest.parent.mkdir(parents=True, exist_ok=True)

    if logger:
        logger.debug(f"Creating symlink: {dest} -> {source}")

    if not dry_run:
        try:
            dest.symlink_to(source)
        except OSError as e:
            if logger:
                logger.error(f"Failed to create symlink: {e}")
            return False

    return True


def remove_symlink(dest: Path, dotfiles_dir: Path, dry_run: bool = False, logger: Optional[Logger] = None) -> bool:
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

        return str(target).startswith(str(dotfiles_dir))
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
