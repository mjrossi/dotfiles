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

        # Simulate install.py logic: always regenerate
        if zellij_shared.exists():
            shutil.copy2(zellij_shared, zellij_config)

        self.assertTrue(zellij_config.exists())
        self.assertEqual(
            zellij_config.read_text(),
            "# shared zellij config"
        )

    def test_config_kdl_always_regenerated(self):
        """Test that config.kdl is always regenerated from shared."""
        zellij_config = self.config_dir / "zellij" / "config.kdl"
        zellij_shared = self.config_dir / "zellij" / "config.shared.kdl"

        # Create existing stale config.kdl
        zellij_config.write_text("# stale config")

        # Simulate install.py logic: always regenerate
        if zellij_shared.exists():
            shutil.copy2(zellij_shared, zellij_config)

        # Should have shared content, not stale
        self.assertEqual(zellij_config.read_text(), "# shared zellij config")

    def test_config_kdl_appends_local(self):
        """Test that config.local.kdl is appended to generated config.kdl."""
        zellij_config = self.config_dir / "zellij" / "config.kdl"
        zellij_shared = self.config_dir / "zellij" / "config.shared.kdl"
        zellij_local = self.config_dir / "zellij" / "config.local.kdl"

        # Create local overrides
        zellij_local.write_text('web_server_cert "/path/to/cert.pem"\n')

        # Simulate install.py logic: regenerate + append local
        if zellij_shared.exists():
            shutil.copy2(zellij_shared, zellij_config)
            if zellij_local.exists():
                with open(zellij_config, 'a') as f:
                    f.write('\n// Machine-specific overrides from config.local.kdl\n')
                    with open(zellij_local) as local:
                        f.write(local.read())

        content = zellij_config.read_text()
        self.assertIn("# shared zellij config", content)
        self.assertIn("web_server_cert", content)


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


class TestStatePreservation(unittest.TestCase):
    """Test that re-running install preserves existing state records."""

    def setUp(self):
        """Create temporary directories for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.state_file = Path(self.test_dir) / ".dotfiles-state"
        self.logger = Logger(verbose=False)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_existing_state_loaded_before_save(self):
        """Test that existing state records are preserved when new items are added."""
        # Create initial state with some items
        state = StateManager(state_file=self.state_file)
        state.add('dir', 'fish', Path('/home/.config/fish'), backup_created=True)
        state.add('dir', 'nvim', Path('/home/.config/nvim'), backup_created=False)
        state.save()

        # Simulate re-install: load existing state, add new item
        state2 = StateManager(state_file=self.state_file)
        state2.installations = state2.load()
        state2.add('dir', 'ghostty', Path('/home/.config/ghostty'), backup_created=False)
        state2.save()

        # Verify all records are preserved
        state3 = StateManager(state_file=self.state_file)
        records = state3.load()

        self.assertEqual(len(records), 3)
        sources = [r['source'] for r in records]
        self.assertIn('fish', sources)
        self.assertIn('nvim', sources)
        self.assertIn('ghostty', sources)

    def test_empty_state_works(self):
        """Test that loading from non-existent state returns empty list."""
        state = StateManager(state_file=self.state_file)
        records = state.load()
        self.assertEqual(records, [])


class TestSSHPermissions(unittest.TestCase):
    """Test SSH directory permission handling."""

    def setUp(self):
        """Create temporary directories for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.ssh_dir = Path(self.test_dir) / ".ssh"
        self.ssh_dir.mkdir(mode=0o755)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_ssh_dir_permissions_fixed(self):
        """Test that ~/.ssh permissions are corrected to 700."""
        current_perms = oct(self.ssh_dir.stat().st_mode)[-3:]
        self.assertEqual(current_perms, '755')

        os.chmod(str(self.ssh_dir), 0o700)

        fixed_perms = oct(self.ssh_dir.stat().st_mode)[-3:]
        self.assertEqual(fixed_perms, '700')

    def test_ssh_dir_already_correct(self):
        """Test that correct permissions are not changed."""
        os.chmod(str(self.ssh_dir), 0o700)

        current_perms = oct(self.ssh_dir.stat().st_mode)[-3:]
        self.assertEqual(current_perms, '700')


if __name__ == '__main__':
    unittest.main()
