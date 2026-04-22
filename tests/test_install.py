#!/usr/bin/env python3
"""
Unit tests for install.py - dotfiles installation script.
"""

import io
import unittest
import tempfile
import shutil
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.common import (
    backup_path, restore_backup, create_symlink, is_managed_symlink,
    Logger, StateManager
)
import install


def _make_args(**overrides):
    """Build an argparse-like Namespace with sensible defaults."""
    defaults = {'dry_run': False, 'verbose': False, 'force': False, 'skip_brew': False}
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _fresh_counters():
    return {'installed': 0, 'skipped': 0, 'backed_up': 0, 'errors': 0}


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


class TestRestoreBackupNumbered(unittest.TestCase):
    """Test that restore_backup picks the most recent (highest-numbered) backup."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.test_dir) / ".config"
        self.config_dir.mkdir()
        self.logger = Logger(verbose=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_restore_picks_highest_numbered_backup(self):
        """With .bak, .bak.1, .bak.2 -- restore should pick .bak.2 (newest)."""
        dest = self.config_dir / "fish"

        bak = self.config_dir / "fish.bak"
        bak.mkdir()
        (bak / "config.fish").write_text("# oldest")

        bak1 = self.config_dir / "fish.bak.1"
        bak1.mkdir()
        (bak1 / "config.fish").write_text("# middle")

        bak2 = self.config_dir / "fish.bak.2"
        bak2.mkdir()
        (bak2 / "config.fish").write_text("# newest")

        result = restore_backup(dest, dry_run=False, logger=self.logger)

        self.assertTrue(result)
        self.assertTrue(dest.exists())
        self.assertEqual((dest / "config.fish").read_text(), "# newest")
        # .bak.2 should be gone (moved to dest), .bak and .bak.1 remain
        self.assertFalse(bak2.exists())
        self.assertTrue(bak.exists())
        self.assertTrue(bak1.exists())

    def test_restore_falls_back_to_bak_when_no_numbered(self):
        """With only .bak (no numbered), restore should pick .bak."""
        dest = self.config_dir / "fish"

        bak = self.config_dir / "fish.bak"
        bak.mkdir()
        (bak / "config.fish").write_text("# only backup")

        result = restore_backup(dest, dry_run=False, logger=self.logger)

        self.assertTrue(result)
        self.assertTrue(dest.exists())
        self.assertEqual((dest / "config.fish").read_text(), "# only backup")
        self.assertFalse(bak.exists())


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


class TestSSHConfigFilePermissions(unittest.TestCase):
    """Test ~/.ssh/config permission handling (600)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ssh_dir = Path(self.test_dir) / ".ssh"
        self.ssh_dir.mkdir(mode=0o700)
        self.ssh_config = self.ssh_dir / "config"
        self.ssh_config.write_text("Host example\n  User me\n")
        os.chmod(str(self.ssh_config), 0o644)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_ssh_config_permissions_fixed(self):
        """Permissions on ~/.ssh/config are corrected to 600."""
        current_perms = oct(os.stat(str(self.ssh_config)).st_mode)[-3:]
        self.assertEqual(current_perms, '644')

        os.chmod(str(self.ssh_config), 0o600)

        fixed_perms = oct(os.stat(str(self.ssh_config)).st_mode)[-3:]
        self.assertEqual(fixed_perms, '600')

    def test_ssh_config_symlink_permissions_fixed(self):
        """install.py also fixes perms when ~/.ssh/config is a symlink to the repo."""
        # Simulate the post-symlink state: ssh/config is a symlink into dotfiles
        dotfiles_ssh_dir = Path(self.test_dir) / "dotfiles" / "ssh"
        dotfiles_ssh_dir.mkdir(parents=True)
        real_config = dotfiles_ssh_dir / "config"
        real_config.write_text("Host example\n  User me\n")
        os.chmod(str(real_config), 0o644)

        self.ssh_config.unlink()
        self.ssh_config.symlink_to(real_config)

        # install.py uses os.stat (follows symlink) and chmods the resolved path
        config_perms = oct(os.stat(str(self.ssh_config)).st_mode)[-3:]
        self.assertEqual(config_perms, '644')

        os.chmod(str(self.ssh_config), 0o600)

        self.assertEqual(oct(os.stat(str(self.ssh_config)).st_mode)[-3:], '600')


class TestProcessItem(unittest.TestCase):
    """Exercise the real install.process_item on a sandboxed filesystem."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dotfiles_dir = Path(self.test_dir) / "dotfiles"
        self.home_dir = Path(self.test_dir) / "home"
        self.config_dir = self.home_dir / ".config"
        self.dotfiles_dir.mkdir()
        self.home_dir.mkdir()
        self.config_dir.mkdir()

        # Source fixtures
        (self.dotfiles_dir / "fish").mkdir()
        (self.dotfiles_dir / "fish" / "config.fish").write_text("# fish")
        (self.dotfiles_dir / "gitconfig").write_text("[user]\n\tname = test\n")

        self.logger = Logger(verbose=False)
        self.state_file = Path(self.test_dir) / ".dotfiles-state"
        self.state = StateManager(state_file=self.state_file)
        # Silence the logger's info/success/header output during tests
        self._stdout_buf = io.StringIO()
        self._stderr_buf = io.StringIO()
        self._stdout_ctx = redirect_stdout(self._stdout_buf)
        self._stderr_ctx = redirect_stderr(self._stderr_buf)
        self._stdout_ctx.__enter__()
        self._stderr_ctx.__enter__()

    def tearDown(self):
        self._stderr_ctx.__exit__(None, None, None)
        self._stdout_ctx.__exit__(None, None, None)
        shutil.rmtree(self.test_dir)

    def _run(self, source_name, dest, kind, args=None):
        counters = _fresh_counters()
        install.process_item(
            source_name, dest, kind, self.dotfiles_dir,
            self.state, args or _make_args(), self.logger, counters,
        )
        return counters

    def test_fresh_install_dir_creates_symlink(self):
        dest = self.config_dir / "fish"
        counters = self._run("fish", dest, "dir")

        self.assertEqual(counters['installed'], 1)
        self.assertEqual(counters['errors'], 0)
        self.assertTrue(dest.is_symlink())
        self.assertEqual(dest.readlink(), self.dotfiles_dir / "fish")
        # State recorded with backup_created=False
        self.assertEqual(len(self.state.installations), 1)
        self.assertEqual(self.state.installations[0]['source'], 'fish')
        self.assertFalse(self.state.installations[0]['backup_created'])

    def test_fresh_install_file_creates_symlink(self):
        dest = self.home_dir / ".gitconfig"
        counters = self._run("gitconfig", dest, "file")

        self.assertEqual(counters['installed'], 1)
        self.assertTrue(dest.is_symlink())

    def test_source_missing_increments_errors(self):
        dest = self.config_dir / "nvim"
        counters = self._run("nvim", dest, "dir")  # no nvim dir in dotfiles

        self.assertEqual(counters['errors'], 1)
        self.assertEqual(counters['installed'], 0)
        self.assertFalse(dest.exists())

    def test_source_type_mismatch_file_not_dir(self):
        # Source 'gitconfig' is a file; requesting kind='dir' should error
        dest = self.config_dir / "gitconfig"
        counters = self._run("gitconfig", dest, "dir")

        self.assertEqual(counters['errors'], 1)
        self.assertFalse(dest.exists())

    def test_source_type_mismatch_dir_not_file(self):
        # Source 'fish' is a dir; requesting kind='file' should error
        dest = self.home_dir / ".fish"
        counters = self._run("fish", dest, "file")

        self.assertEqual(counters['errors'], 1)
        self.assertFalse(dest.exists())

    def test_already_installed_is_skipped(self):
        dest = self.config_dir / "fish"
        dest.symlink_to(self.dotfiles_dir / "fish")

        counters = self._run("fish", dest, "dir")

        self.assertEqual(counters['skipped'], 1)
        self.assertEqual(counters['installed'], 0)
        self.assertEqual(counters['backed_up'], 0)

    def test_existing_directory_is_backed_up(self):
        dest = self.config_dir / "fish"
        dest.mkdir()
        (dest / "old.fish").write_text("# pre-existing")

        counters = self._run("fish", dest, "dir")

        self.assertEqual(counters['installed'], 1)
        self.assertEqual(counters['backed_up'], 1)
        self.assertTrue(dest.is_symlink())
        backup = self.config_dir / "fish.bak"
        self.assertTrue(backup.is_dir())
        self.assertTrue((backup / "old.fish").exists())
        # State records backup_created=True
        self.assertTrue(self.state.installations[0]['backup_created'])

    def test_dest_file_but_kind_dir_errors(self):
        dest = self.config_dir / "fish"
        dest.write_text("stray file")

        counters = self._run("fish", dest, "dir")

        self.assertEqual(counters['errors'], 1)
        # Stray file left untouched (not backed up, not replaced)
        self.assertTrue(dest.is_file())

    def test_dest_dir_but_kind_file_errors(self):
        dest = self.home_dir / ".gitconfig"
        dest.mkdir()

        counters = self._run("gitconfig", dest, "file")

        self.assertEqual(counters['errors'], 1)
        self.assertTrue(dest.is_dir())
        self.assertFalse(dest.is_symlink())

    def test_broken_symlink_is_replaced(self):
        dest = self.config_dir / "fish"
        dest.symlink_to(self.dotfiles_dir / "does-not-exist")
        self.assertTrue(dest.is_symlink())
        self.assertFalse(dest.exists())

        counters = self._run("fish", dest, "dir")

        self.assertEqual(counters['installed'], 1)
        self.assertTrue(dest.is_symlink())
        self.assertEqual(dest.readlink(), self.dotfiles_dir / "fish")

    def test_dry_run_does_not_create_symlink(self):
        dest = self.config_dir / "fish"

        counters = self._run("fish", dest, "dir", args=_make_args(dry_run=True))

        self.assertEqual(counters['installed'], 1)
        self.assertFalse(dest.exists())
        # No state record written on dry-run
        self.assertEqual(len(self.state.installations), 0)


class TestInstallBrewfile(unittest.TestCase):
    """Exercise install.install_brewfile opt-out and short-circuit paths."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dotfiles_dir = Path(self.test_dir) / "dotfiles"
        self.dotfiles_dir.mkdir()
        self.logger = Logger(verbose=False)
        # Silence info/header output
        self._stdout_buf = io.StringIO()
        self._stdout_ctx = redirect_stdout(self._stdout_buf)
        self._stdout_ctx.__enter__()

    def tearDown(self):
        self._stdout_ctx.__exit__(None, None, None)
        shutil.rmtree(self.test_dir)

    def test_skip_brew_flag_short_circuits(self):
        (self.dotfiles_dir / "Brewfile").write_text("brew 'mise'\n")

        with mock.patch('install.subprocess.run') as mock_run, \
             mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('DOTFILES_SKIP_BREW', None)
            install.install_brewfile(self.dotfiles_dir, _make_args(skip_brew=True), self.logger)

        mock_run.assert_not_called()

    def test_env_var_opt_out_short_circuits(self):
        (self.dotfiles_dir / "Brewfile").write_text("brew 'mise'\n")

        with mock.patch('install.subprocess.run') as mock_run, \
             mock.patch.dict(os.environ, {'DOTFILES_SKIP_BREW': '1'}):
            install.install_brewfile(self.dotfiles_dir, _make_args(), self.logger)

        mock_run.assert_not_called()

    def test_missing_brewfile_is_silent_noop(self):
        # No Brewfile in self.dotfiles_dir
        with mock.patch('install.subprocess.run') as mock_run, \
             mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('DOTFILES_SKIP_BREW', None)
            install.install_brewfile(self.dotfiles_dir, _make_args(), self.logger)

        mock_run.assert_not_called()

    def test_brew_not_on_path_returns_silently(self):
        (self.dotfiles_dir / "Brewfile").write_text("brew 'mise'\n")

        with mock.patch('install.subprocess.run') as mock_run, \
             mock.patch('install.shutil.which', return_value=None), \
             mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('DOTFILES_SKIP_BREW', None)
            install.install_brewfile(self.dotfiles_dir, _make_args(), self.logger)

        mock_run.assert_not_called()

    def test_satisfied_brewfile_skips_install(self):
        (self.dotfiles_dir / "Brewfile").write_text("brew 'mise'\n")
        check_result = subprocess.CompletedProcess(args=[], returncode=0, stdout='', stderr='')

        with mock.patch('install.subprocess.run', return_value=check_result) as mock_run, \
             mock.patch('install.shutil.which', return_value='/usr/local/bin/brew'), \
             mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('DOTFILES_SKIP_BREW', None)
            install.install_brewfile(self.dotfiles_dir, _make_args(), self.logger)

        # Only the check should have run, not a bundle install
        self.assertEqual(mock_run.call_count, 1)
        called_args = mock_run.call_args.args[0]
        self.assertIn('check', called_args)

    def test_dry_run_with_unsatisfied_brewfile_does_not_install(self):
        (self.dotfiles_dir / "Brewfile").write_text("brew 'mise'\n")
        check_result = subprocess.CompletedProcess(args=[], returncode=1, stdout='', stderr='')

        with mock.patch('install.subprocess.run', return_value=check_result) as mock_run, \
             mock.patch('install.shutil.which', return_value='/usr/local/bin/brew'), \
             mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('DOTFILES_SKIP_BREW', None)
            install.install_brewfile(self.dotfiles_dir, _make_args(dry_run=True), self.logger)

        # Only the check should have run — no install in dry-run mode
        self.assertEqual(mock_run.call_count, 1)
        called_args = mock_run.call_args.args[0]
        self.assertIn('check', called_args)
        self.assertNotIn('install', called_args)


if __name__ == '__main__':
    unittest.main()
