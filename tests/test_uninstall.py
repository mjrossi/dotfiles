#!/usr/bin/env python3
"""
Unit tests for uninstall.py - dotfiles uninstallation script.
"""

import io
import unittest
import tempfile
import shutil
from contextlib import redirect_stderr
from pathlib import Path
import sys

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.common import (
    restore_backup, remove_symlink, is_managed_symlink,
    Logger
)


class TestUninstallWithBackups(unittest.TestCase):
    """Test uninstallation when backups exist."""

    def setUp(self):
        """Create temporary directories with symlinks and backups."""
        self.test_dir = tempfile.mkdtemp()
        self.dotfiles_dir = Path(self.test_dir) / "dotfiles"
        self.home_dir = Path(self.test_dir) / "home"
        self.config_dir = self.home_dir / ".config"

        # Create directory structure
        self.dotfiles_dir.mkdir()
        self.home_dir.mkdir()
        self.config_dir.mkdir()

        # Create fake dotfiles
        fish_dir = self.dotfiles_dir / "fish"
        fish_dir.mkdir()
        (fish_dir / "config.fish").write_text("# new fish config")

        # Create backup
        fish_backup = self.config_dir / "fish.bak"
        fish_backup.mkdir()
        (fish_backup / "config.fish").write_text("# old fish config")

        # Create symlink
        (self.config_dir / "fish").symlink_to(fish_dir)

        self.logger = Logger(verbose=False)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_symlink_removal(self):
        """Test that managed symlinks are removed."""
        dest = self.config_dir / "fish"

        self.assertTrue(dest.is_symlink())

        result = remove_symlink(dest, self.dotfiles_dir, dry_run=False, logger=self.logger)

        self.assertTrue(result)
        self.assertFalse(dest.exists())

    def test_backup_restoration(self):
        """Test that backups are restored after symlink removal."""
        dest = self.config_dir / "fish"

        # Remove symlink
        remove_symlink(dest, self.dotfiles_dir, dry_run=False, logger=self.logger)

        # Restore backup
        result = restore_backup(dest, dry_run=False, logger=self.logger)

        self.assertTrue(result)
        self.assertTrue(dest.exists())
        self.assertTrue(dest.is_dir())
        self.assertTrue((dest / "config.fish").exists())
        self.assertEqual(
            (dest / "config.fish").read_text(),
            "# old fish config"
        )


class TestUninstallFreshMachine(unittest.TestCase):
    """Test uninstallation on fresh machine (no backups)."""

    def setUp(self):
        """Create temporary directories with symlinks but no backups."""
        self.test_dir = tempfile.mkdtemp()
        self.dotfiles_dir = Path(self.test_dir) / "dotfiles"
        self.home_dir = Path(self.test_dir) / "home"
        self.config_dir = self.home_dir / ".config"

        # Create directory structure
        self.dotfiles_dir.mkdir()
        self.home_dir.mkdir()
        self.config_dir.mkdir()

        # Create fake dotfiles
        fish_dir = self.dotfiles_dir / "fish"
        fish_dir.mkdir()
        (fish_dir / "config.fish").write_text("# fish config")

        # Create symlink (no backup)
        (self.config_dir / "fish").symlink_to(fish_dir)

        self.logger = Logger(verbose=False)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_uninstall_without_backup(self):
        """Test that uninstall works when no backup exists."""
        dest = self.config_dir / "fish"

        # Remove symlink
        result = remove_symlink(dest, self.dotfiles_dir, dry_run=False, logger=self.logger)

        self.assertTrue(result)
        self.assertFalse(dest.exists())

        # Try to restore backup (should fail gracefully)
        backup_restored = restore_backup(dest, dry_run=False, logger=self.logger)

        self.assertFalse(backup_restored)
        self.assertFalse(dest.exists())


class TestMachineSpecificFilePreservation(unittest.TestCase):
    """Test preservation of machine-specific config files."""

    def setUp(self):
        """Create temporary directories with machine-specific files."""
        self.test_dir = tempfile.mkdtemp()
        self.dotfiles_dir = Path(self.test_dir) / "dotfiles"
        self.home_dir = Path(self.test_dir) / "home"
        self.config_dir = self.home_dir / ".config"

        # Create directory structure
        self.dotfiles_dir.mkdir()
        self.home_dir.mkdir()
        self.config_dir.mkdir()

        # Create fake dotfiles with machine-specific files
        fish_dir = self.dotfiles_dir / "fish"
        fish_dir.mkdir()
        (fish_dir / "config.fish").write_text("# fish config")
        (fish_dir / "config.local.fish").write_text("# machine-specific")

        zellij_dir = self.dotfiles_dir / "zellij"
        zellij_dir.mkdir()
        (zellij_dir / "config.shared.kdl").write_text("# shared")
        (zellij_dir / "config.kdl").write_text("# machine-specific")

        # Create symlinks
        (self.config_dir / "fish").symlink_to(fish_dir)
        (self.config_dir / "zellij").symlink_to(zellij_dir)

        self.logger = Logger(verbose=False)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_preserve_fish_local_config(self):
        """Test that fish/config.local.fish is preserved during uninstall."""
        fish_dest = self.config_dir / "fish"
        local_config = self.dotfiles_dir / "fish" / "config.local.fish"

        # Machine-specific file should exist in symlinked directory
        self.assertTrue(local_config.exists())

        # Simulate uninstall.py logic
        files_to_preserve = []
        if local_config.exists() and local_config.is_file():
            files_to_preserve.append({
                'source': local_config,
                'dest': fish_dest,
                'filename': 'config.local.fish'
            })

        # Remove symlink
        remove_symlink(fish_dest, self.dotfiles_dir, dry_run=False, logger=self.logger)

        # Create target directory (no backup scenario)
        fish_dest.mkdir(parents=True, exist_ok=True)

        # Copy preserved files
        for item in files_to_preserve:
            target = item['dest'] / item['filename']
            shutil.copy2(item['source'], target)

        # Verify preserved file exists in new location
        preserved_file = fish_dest / "config.local.fish"
        self.assertTrue(preserved_file.exists())
        self.assertEqual(preserved_file.read_text(), "# machine-specific")

    def test_preserve_zellij_config_kdl(self):
        """Test that zellij/config.kdl is preserved during uninstall."""
        zellij_dest = self.config_dir / "zellij"
        config_kdl = self.dotfiles_dir / "zellij" / "config.kdl"

        # Machine-specific file should exist
        self.assertTrue(config_kdl.exists())

        # Simulate uninstall.py logic
        files_to_preserve = []
        if config_kdl.exists() and config_kdl.is_file():
            files_to_preserve.append({
                'source': config_kdl,
                'dest': zellij_dest,
                'filename': 'config.kdl'
            })

        # Remove symlink
        remove_symlink(zellij_dest, self.dotfiles_dir, dry_run=False, logger=self.logger)

        # Create target directory (no backup scenario)
        zellij_dest.mkdir(parents=True, exist_ok=True)

        # Copy preserved files
        for item in files_to_preserve:
            target = item['dest'] / item['filename']
            shutil.copy2(item['source'], target)

        # Verify preserved file exists
        preserved_file = zellij_dest / "config.kdl"
        self.assertTrue(preserved_file.exists())
        self.assertEqual(preserved_file.read_text(), "# machine-specific")

    def test_preserve_with_backup_restoration(self):
        """Test file preservation when backup is also restored."""
        fish_dest = self.config_dir / "fish"
        local_config = self.dotfiles_dir / "fish" / "config.local.fish"

        # Create backup
        fish_backup = self.config_dir / "fish.bak"
        fish_backup.mkdir()
        (fish_backup / "config.fish").write_text("# old config")

        # Collect files to preserve
        files_to_preserve = []
        if local_config.exists():
            files_to_preserve.append({
                'source': local_config,
                'dest': fish_dest,
                'filename': 'config.local.fish'
            })

        # Remove symlink
        remove_symlink(fish_dest, self.dotfiles_dir, dry_run=False, logger=self.logger)

        # Restore backup
        restore_backup(fish_dest, dry_run=False, logger=self.logger)

        # Copy preserved files
        for item in files_to_preserve:
            target = item['dest'] / item['filename']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item['source'], target)

        # Verify both backup and preserved file exist
        self.assertTrue(fish_dest.exists())
        self.assertTrue((fish_dest / "config.fish").exists())  # From backup
        self.assertTrue((fish_dest / "config.local.fish").exists())  # Preserved


class TestDryRunMode(unittest.TestCase):
    """Test that dry-run mode doesn't modify filesystem."""

    def setUp(self):
        """Create temporary directories for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.dotfiles_dir = Path(self.test_dir) / "dotfiles"
        self.home_dir = Path(self.test_dir) / "home"
        self.config_dir = self.home_dir / ".config"

        # Create directory structure
        self.dotfiles_dir.mkdir()
        self.home_dir.mkdir()
        self.config_dir.mkdir()

        # Create existing config
        existing_fish = self.config_dir / "fish"
        existing_fish.mkdir()
        (existing_fish / "config.fish").write_text("# existing")

        self.logger = Logger(verbose=False)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_backup_dry_run_no_changes(self):
        """Test that dry-run mode doesn't actually move files."""
        from lib.common import backup_path

        dest = self.config_dir / "fish"
        original_exists = dest.exists()

        backup = backup_path(dest, dry_run=True, logger=self.logger)

        # Should still exist (not moved)
        self.assertEqual(dest.exists(), original_exists)
        # Backup path should be returned but not exist
        if backup:
            self.assertFalse(backup.exists())


class TestRemoveSymlinkRefusesExternal(unittest.TestCase):
    """Safety: uninstall must never remove a symlink pointing outside dotfiles."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)
        self.dotfiles_dir = self.root / "dotfiles"
        self.dotfiles_dir.mkdir()
        self.logger = Logger(verbose=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_external_symlink_is_not_removed(self):
        # Simulates a state entry pointing at a symlink the user created
        # that targets something outside the dotfiles repo.
        external_target = self.root / "other-repo" / "config"
        external_target.mkdir(parents=True)
        dest = self.root / "home-symlink"
        dest.symlink_to(external_target)

        with redirect_stderr(io.StringIO()):
            result = remove_symlink(dest, self.dotfiles_dir,
                                    dry_run=False, logger=self.logger)

        self.assertFalse(result)
        self.assertTrue(dest.is_symlink(), "external symlink must not be removed")


class TestRestoreBackupMissing(unittest.TestCase):
    """restore_backup returns False cleanly when no backup exists."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.test_dir)
        self.logger = Logger(verbose=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_returns_false_when_no_backup(self):
        dest = self.config_dir / "fish"

        result = restore_backup(dest, dry_run=False, logger=self.logger)

        self.assertFalse(result)
        self.assertFalse(dest.exists())

    def test_dry_run_returns_false_when_no_backup(self):
        dest = self.config_dir / "fish"

        result = restore_backup(dest, dry_run=True, logger=self.logger)

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
