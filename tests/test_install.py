#!/usr/bin/env python3
"""
Unit tests for install.py - dotfiles installation script.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.common import (
    backup_path, create_symlink, is_managed_symlink,
    Logger, StateManager
)


class TestFreshInstall(unittest.TestCase):
    """Test installation on a fresh machine with no existing configs."""

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

        # Create fake dotfiles
        (self.dotfiles_dir / "fish").mkdir()
        (self.dotfiles_dir / "fish" / "config.fish").write_text("# fish config")

        self.logger = Logger(verbose=False)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_symlink_creation_no_existing_config(self):
        """Test creating symlink when no config exists."""
        source = self.dotfiles_dir / "fish"
        dest = self.config_dir / "fish"

        result = create_symlink(source, dest, dry_run=False, logger=self.logger)

        self.assertTrue(result)
        self.assertTrue(dest.is_symlink())
        self.assertEqual(dest.readlink(), source)

    def test_no_backup_created_on_fresh_install(self):
        """Test that no backup is created when no existing config exists."""
        dest = self.config_dir / "fish"

        # No existing file/directory
        self.assertFalse(dest.exists())

        backup = backup_path(dest, dry_run=False, logger=self.logger)

        self.assertIsNone(backup)

    def test_is_managed_symlink_returns_true(self):
        """Test that symlinks pointing to dotfiles are recognized as managed."""
        source = self.dotfiles_dir / "fish"
        dest = self.config_dir / "fish"

        create_symlink(source, dest, dry_run=False, logger=self.logger)

        self.assertTrue(is_managed_symlink(dest, self.dotfiles_dir))


class TestInstallWithExistingConfigs(unittest.TestCase):
    """Test installation when existing configs already exist."""

    def setUp(self):
        """Create temporary directories with existing configs."""
        self.test_dir = tempfile.mkdtemp()
        self.dotfiles_dir = Path(self.test_dir) / "dotfiles"
        self.home_dir = Path(self.test_dir) / "home"
        self.config_dir = self.home_dir / ".config"

        # Create directory structure
        self.dotfiles_dir.mkdir()
        self.home_dir.mkdir()
        self.config_dir.mkdir()

        # Create fake dotfiles
        (self.dotfiles_dir / "fish").mkdir()
        (self.dotfiles_dir / "fish" / "config.fish").write_text("# new fish config")

        # Create existing config
        existing_fish = self.config_dir / "fish"
        existing_fish.mkdir()
        (existing_fish / "config.fish").write_text("# old fish config")

        self.logger = Logger(verbose=False)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_backup_created_for_existing_directory(self):
        """Test that existing directory is backed up before symlinking."""
        dest = self.config_dir / "fish"

        backup = backup_path(dest, dry_run=False, logger=self.logger)

        self.assertIsNotNone(backup)
        self.assertTrue(backup.exists())
        self.assertEqual(backup.name, "fish.bak")
        self.assertTrue((backup / "config.fish").exists())

    def test_backup_numbering_when_backup_exists(self):
        """Test that backups are numbered when .bak already exists."""
        dest = self.config_dir / "fish"

        # Create first backup
        backup1 = backup_path(dest, dry_run=False, logger=self.logger)

        # Recreate original
        dest.mkdir()
        (dest / "config.fish").write_text("# old fish config 2")

        # Create second backup
        backup2 = backup_path(dest, dry_run=False, logger=self.logger)

        self.assertEqual(backup1.name, "fish.bak")
        self.assertEqual(backup2.name, "fish.bak.1")


class TestZellijSpecialHandling(unittest.TestCase):
    """Test special handling for zellij config.kdl creation."""

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

        # Create zellij dotfiles
        zellij_dir = self.dotfiles_dir / "zellij"
        zellij_dir.mkdir()
        (zellij_dir / "config.shared.kdl").write_text("# shared zellij config")
        (zellij_dir / "config.kdl.template").write_text("# template")

        # Symlink zellij directory
        zellij_dest = self.config_dir / "zellij"
        zellij_dest.symlink_to(zellij_dir)

        self.logger = Logger(verbose=False)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_config_kdl_created_from_shared(self):
        """Test that config.kdl is created from config.shared.kdl."""
        zellij_config = self.config_dir / "zellij" / "config.kdl"
        zellij_shared = self.config_dir / "zellij" / "config.shared.kdl"

        # Simulate install.py logic
        if zellij_shared.exists() and not zellij_config.exists():
            shutil.copy2(zellij_shared, zellij_config)

        self.assertTrue(zellij_config.exists())
        self.assertEqual(
            zellij_config.read_text(),
            "# shared zellij config"
        )

    def test_config_kdl_not_overwritten_if_exists(self):
        """Test that existing config.kdl is not overwritten."""
        zellij_config = self.config_dir / "zellij" / "config.kdl"
        zellij_shared = self.config_dir / "zellij" / "config.shared.kdl"

        # Create existing config.kdl
        zellij_config.write_text("# custom config")

        # Simulate install.py logic
        if zellij_shared.exists() and not zellij_config.exists():
            shutil.copy2(zellij_shared, zellij_config)

        # Should still have custom content
        self.assertEqual(zellij_config.read_text(), "# custom config")


class TestIdempotency(unittest.TestCase):
    """Test that install script can be run multiple times safely."""

    def setUp(self):
        """Create temporary directories with symlinks already installed."""
        self.test_dir = tempfile.mkdtemp()
        self.dotfiles_dir = Path(self.test_dir) / "dotfiles"
        self.home_dir = Path(self.test_dir) / "home"
        self.config_dir = self.home_dir / ".config"

        # Create directory structure
        self.dotfiles_dir.mkdir()
        self.home_dir.mkdir()
        self.config_dir.mkdir()

        # Create fake dotfiles
        (self.dotfiles_dir / "fish").mkdir()
        (self.dotfiles_dir / "fish" / "config.fish").write_text("# fish config")

        # Create symlink (already installed)
        (self.config_dir / "fish").symlink_to(self.dotfiles_dir / "fish")

        self.logger = Logger(verbose=False)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_already_installed_symlink_detected(self):
        """Test that already installed symlinks are detected and skipped."""
        source = self.dotfiles_dir / "fish"
        dest = self.config_dir / "fish"

        # Check if already installed
        is_installed = (
            dest.is_symlink() and
            is_managed_symlink(dest, self.dotfiles_dir) and
            dest.readlink() == source
        )

        self.assertTrue(is_installed)


if __name__ == '__main__':
    unittest.main()
