#!/usr/bin/env python3
"""
Unit tests for uninstall.py - dotfiles uninstallation script.
"""

import io
import unittest
import tempfile
import shutil
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import sys

# Add repo root to path so `lib`, `uninstall`, and `tests._helpers` all import
# whether we're running via `python3 -m unittest discover` or `python3 tests/test_uninstall.py`.
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests._helpers import DotfilesTestCase

from lib.common import (
    restore_backup, remove_symlink, is_managed_symlink,
    Logger
)
import uninstall


class TestUninstallWithBackups(DotfilesTestCase):
    """Test uninstallation when backups exist."""

    def setUp(self):
        super().setUp()
        fish_dir = self.dotfiles_dir / "fish"
        fish_dir.mkdir()
        (fish_dir / "config.fish").write_text("# new fish config")

        fish_backup = self.config_dir / "fish.bak"
        fish_backup.mkdir()
        (fish_backup / "config.fish").write_text("# old fish config")

        (self.config_dir / "fish").symlink_to(fish_dir)

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


class TestUninstallFreshMachine(DotfilesTestCase):
    """Test uninstallation on fresh machine (no backups)."""

    def setUp(self):
        super().setUp()
        fish_dir = self.dotfiles_dir / "fish"
        fish_dir.mkdir()
        (fish_dir / "config.fish").write_text("# fish config")
        (self.config_dir / "fish").symlink_to(fish_dir)

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


class TestMachineSpecificFilePreservation(DotfilesTestCase):
    """Exercise uninstall.find_preserved_file + preserve_file on real state."""

    def setUp(self):
        super().setUp()
        # Dotfiles sources with machine-specific files alongside the shared ones
        fish_dir = self.dotfiles_dir / "fish"
        fish_dir.mkdir()
        (fish_dir / "config.fish").write_text("# fish config")
        (fish_dir / "config.local.fish").write_text("# machine-specific")

        zellij_dir = self.dotfiles_dir / "zellij"
        zellij_dir.mkdir()
        (zellij_dir / "config.shared.kdl").write_text("# shared")
        (zellij_dir / "config.kdl").write_text("# machine-specific")

        # Post-install state: destinations are symlinks to the dotfiles dirs
        (self.config_dir / "fish").symlink_to(fish_dir)
        (self.config_dir / "zellij").symlink_to(zellij_dir)

        # Silence uninstall helpers' info-level output
        self._stdout_ctx = redirect_stdout(io.StringIO())
        self._stdout_ctx.__enter__()

    def tearDown(self):
        self._stdout_ctx.__exit__(None, None, None)
        super().tearDown()

    def test_preserve_fish_local_config(self):
        fish_dest = self.config_dir / "fish"

        found = uninstall.find_preserved_file(
            'fish', 'dir', fish_dest, self.dotfiles_dir
        )
        self.assertIsNotNone(found)
        self.assertEqual(found['filename'], 'config.local.fish')
        self.assertEqual(found['source'], self.dotfiles_dir / "fish" / "config.local.fish")

        remove_symlink(fish_dest, self.dotfiles_dir, dry_run=False, logger=self.logger)

        ok = uninstall.preserve_file(found, fish_dest, dry_run=False, logger=self.logger)

        self.assertTrue(ok)
        preserved_file = fish_dest / "config.local.fish"
        self.assertTrue(preserved_file.exists())
        self.assertEqual(preserved_file.read_text(), "# machine-specific")

    def test_preserve_zellij_config_kdl(self):
        zellij_dest = self.config_dir / "zellij"

        found = uninstall.find_preserved_file(
            'zellij', 'dir', zellij_dest, self.dotfiles_dir
        )
        self.assertIsNotNone(found)
        self.assertEqual(found['filename'], 'config.kdl')

        remove_symlink(zellij_dest, self.dotfiles_dir, dry_run=False, logger=self.logger)

        ok = uninstall.preserve_file(found, zellij_dest, dry_run=False, logger=self.logger)

        self.assertTrue(ok)
        preserved_file = zellij_dest / "config.kdl"
        self.assertTrue(preserved_file.exists())
        self.assertEqual(preserved_file.read_text(), "# machine-specific")

    def test_preserve_with_backup_restoration(self):
        fish_dest = self.config_dir / "fish"

        # Backup that uninstall will restore after removing the symlink
        fish_backup = self.config_dir / "fish.bak"
        fish_backup.mkdir()
        (fish_backup / "config.fish").write_text("# old config")

        found = uninstall.find_preserved_file(
            'fish', 'dir', fish_dest, self.dotfiles_dir
        )

        remove_symlink(fish_dest, self.dotfiles_dir, dry_run=False, logger=self.logger)
        restore_backup(fish_dest, dry_run=False, logger=self.logger)
        uninstall.preserve_file(found, fish_dest, dry_run=False, logger=self.logger)

        self.assertTrue(fish_dest.exists())
        self.assertTrue((fish_dest / "config.fish").exists())          # from backup
        self.assertTrue((fish_dest / "config.local.fish").exists())    # preserved

    def test_find_returns_none_for_unknown_source(self):
        # Non-dir entries and sources without a registered preserved file → None
        file_dest = self.home_dir / ".gitconfig"
        self.assertIsNone(
            uninstall.find_preserved_file('gitconfig', 'file', file_dest, self.dotfiles_dir)
        )
        nvim_dest = self.config_dir / "nvim"
        self.assertIsNone(
            uninstall.find_preserved_file('nvim', 'dir', nvim_dest, self.dotfiles_dir)
        )

    def test_find_returns_none_when_local_file_missing(self):
        # fish source exists, but no config.local.fish in it
        (self.dotfiles_dir / "fish" / "config.local.fish").unlink()
        fish_dest = self.config_dir / "fish"

        self.assertIsNone(
            uninstall.find_preserved_file('fish', 'dir', fish_dest, self.dotfiles_dir)
        )

    def test_find_returns_none_when_dest_not_symlink(self):
        # Replace the fish symlink with a real directory
        fish_dest = self.config_dir / "fish"
        fish_dest.unlink()
        fish_dest.mkdir()

        self.assertIsNone(
            uninstall.find_preserved_file('fish', 'dir', fish_dest, self.dotfiles_dir)
        )

    def test_preserve_dry_run_does_not_copy(self):
        fish_dest = self.config_dir / "fish"
        found = uninstall.find_preserved_file(
            'fish', 'dir', fish_dest, self.dotfiles_dir
        )

        remove_symlink(fish_dest, self.dotfiles_dir, dry_run=False, logger=self.logger)

        ok = uninstall.preserve_file(found, fish_dest, dry_run=True, logger=self.logger)

        # Returns True (counted as "would preserve") but nothing written
        self.assertTrue(ok)
        self.assertFalse(fish_dest.exists())


class TestDryRunMode(DotfilesTestCase):
    """Test that dry-run mode doesn't modify filesystem."""

    def setUp(self):
        super().setUp()
        existing_fish = self.config_dir / "fish"
        existing_fish.mkdir()
        (existing_fish / "config.fish").write_text("# existing")

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
