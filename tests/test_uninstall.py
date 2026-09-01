#!/usr/bin/env python3
"""
Unit tests for uninstall.py - dotfiles uninstallation script.
"""

import io
import json
import os
import unittest
import tempfile
import shutil
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import sys
from unittest import mock

# Add repo root to path so `lib`, `uninstall`, and `tests._helpers` all import
# whether we're running via `python3 -m unittest discover` or `python3 tests/test_uninstall.py`.
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests._helpers import DotfilesTestCase

from lib.common import (
    restore_backup, remove_symlink, is_managed_symlink,
    Logger
)
import install
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


class TestRecordedBackupRestoration(DotfilesTestCase):
    """Uninstall restores only the backup recorded by its matching install."""

    def _run_uninstall(self, state_items):
        state_file = Path(self.test_dir) / '.dotfiles-state'
        state_file.write_text(json.dumps({'version': '1.1', 'installed': state_items}))
        with mock.patch.object(uninstall, 'get_dotfiles_dir', return_value=self.dotfiles_dir), \
             mock.patch.object(sys, 'argv', ['uninstall.py', '--force']), \
             mock.patch.dict(os.environ, {'DOTFILES_STATE_FILE': str(state_file)}), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                uninstall.main()
        self.assertEqual(raised.exception.code, 0)

    def test_does_not_restore_stale_backup_when_install_created_none(self):
        source = self.dotfiles_dir / 'fish'
        source.mkdir()
        dest = self.config_dir / 'fish'
        dest.symlink_to(source)
        stale = self.config_dir / 'fish.bak'
        stale.mkdir()
        (stale / 'marker').write_text('unrelated')

        self._run_uninstall([{
            'type': 'dir',
            'source': 'fish',
            'destination': str(dest),
            'backup_created': False,
        }])

        self.assertFalse(dest.exists())
        self.assertTrue(stale.exists())

    def test_restores_exact_recorded_backup_not_newer_stale_backup(self):
        source = self.dotfiles_dir / 'fish'
        source.mkdir()
        dest = self.config_dir / 'fish'
        dest.symlink_to(source)
        recorded = self.config_dir / 'fish.bak'
        recorded.mkdir()
        (recorded / 'marker').write_text('recorded')
        stale = self.config_dir / 'fish.bak.1'
        stale.mkdir()
        (stale / 'marker').write_text('unrelated')

        self._run_uninstall([{
            'type': 'dir',
            'source': 'fish',
            'destination': str(dest),
            'backup_created': True,
            'backup_path': str(recorded),
        }])

        self.assertEqual((dest / 'marker').read_text(), 'recorded')
        self.assertTrue(stale.exists())


class TestReinstallPreservesRecordedBackup(DotfilesTestCase):
    """A reinstall that takes no new backup must not orphan the first one.

    `state.add` replaces records keyed by destination, so the two install paths
    that remove a symlink without backing anything up -- relinking a renamed
    source, and replacing a symlink left broken by a moved repo -- used to
    overwrite the recorded `backup_path` with null. The user's pre-dotfiles
    directory was still on disk, but uninstall no longer knew its name and
    silently left it there.
    """

    def setUp(self):
        super().setUp()
        self.state_file = Path(self.test_dir) / '.dotfiles-state'
        self.dest = self.config_dir / 'fish'

    def _run_install(self, dotfiles_dir, config_dirs):
        with mock.patch.object(install, 'CONFIG_DIRS', config_dirs), \
             mock.patch.object(install, 'CONFIG_FILES', {}), \
             mock.patch.object(install, 'get_dotfiles_dir', return_value=dotfiles_dir), \
             mock.patch.object(install, 'fix_ssh_permissions'), \
             mock.patch.object(install, 'generate_zellij_config', return_value=None), \
             mock.patch.object(install, 'bootstrap_launch_agents'), \
             mock.patch.object(install, 'install_brewfile', return_value=True), \
             mock.patch.object(sys, 'argv', ['install.py', '--force']), \
             mock.patch.dict(os.environ, {'DOTFILES_STATE_FILE': str(self.state_file)}), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                install.main()
        self.assertEqual(raised.exception.code, 0)

    def _run_uninstall(self, dotfiles_dir):
        with mock.patch.object(uninstall, 'get_dotfiles_dir', return_value=dotfiles_dir), \
             mock.patch.object(sys, 'argv', ['uninstall.py', '--force']), \
             mock.patch.dict(os.environ, {'DOTFILES_STATE_FILE': str(self.state_file)}), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                uninstall.main()
        self.assertEqual(raised.exception.code, 0)

    def _seed_user_config(self):
        """The pre-dotfiles directory the first install has to back up."""
        self.dest.mkdir()
        (self.dest / 'config.fish').write_text('# the user\'s own config')

    def _recorded(self):
        installed = json.loads(self.state_file.read_text())['installed']
        return next(r for r in installed if r['destination'] == str(self.dest))

    def test_relinking_a_renamed_source_keeps_the_first_backup(self):
        (self.dotfiles_dir / 'fish').mkdir()
        (self.dotfiles_dir / 'fish_new').mkdir()
        self._seed_user_config()

        self._run_install(self.dotfiles_dir, {'fish': self.dest})
        first = self._recorded()
        self.assertEqual(first['backup_path'], str(self.config_dir / 'fish.bak'))

        # Source renamed in CONFIG_DIRS: the symlink is still managed but now
        # points at the wrong source, so install relinks without backing up.
        self._run_install(self.dotfiles_dir, {'fish_new': self.dest})
        after = self._recorded()
        self.assertEqual(after['source'], 'fish_new')
        self.assertEqual(after['backup_path'], first['backup_path'])
        self.assertTrue(after['backup_created'])

        self._run_uninstall(self.dotfiles_dir)

        self.assertEqual(
            (self.dest / 'config.fish').read_text(), "# the user's own config"
        )
        self.assertFalse((self.config_dir / 'fish.bak').exists())

    def test_reinstall_from_a_moved_repo_keeps_the_first_backup(self):
        (self.dotfiles_dir / 'fish').mkdir()
        self._seed_user_config()

        self._run_install(self.dotfiles_dir, {'fish': self.dest})
        first = self._recorded()
        self.assertEqual(first['backup_path'], str(self.config_dir / 'fish.bak'))

        # Checkout moved: the old symlink now dangles outside the new repo, so
        # install removes it as a broken symlink -- again with no new backup.
        moved = Path(self.test_dir) / 'dotfiles-moved'
        shutil.move(self.dotfiles_dir, moved)
        (moved / 'fish').mkdir(exist_ok=True)
        self.assertTrue(self.dest.is_symlink())
        self.assertFalse(self.dest.exists())

        self._run_install(moved, {'fish': self.dest})
        after = self._recorded()
        self.assertEqual(after['backup_path'], first['backup_path'])
        self.assertTrue(after['backup_created'])

        self._run_uninstall(moved)

        self.assertEqual(
            (self.dest / 'config.fish').read_text(), "# the user's own config"
        )
        self.assertFalse((self.config_dir / 'fish.bak').exists())


class TestOwnedBackup(DotfilesTestCase):
    """The preview, the leftover report, and the restore agree on one file."""

    def test_legacy_record_discovers_highest_numbered_backup(self):
        dest = self.config_dir / 'fish'
        (self.config_dir / 'fish.bak').mkdir()
        (self.config_dir / 'fish.bak.1').mkdir()

        owned = uninstall.owned_backup(
            {'dest': dest, 'backup_created': True}
        )

        self.assertEqual(owned, self.config_dir / 'fish.bak.1')

    def test_recorded_path_wins_over_discovery(self):
        dest = self.config_dir / 'fish'
        (self.config_dir / 'fish.bak').mkdir()
        (self.config_dir / 'fish.bak.1').mkdir()

        owned = uninstall.owned_backup({
            'dest': dest,
            'backup_created': True,
            'backup_path': str(self.config_dir / 'fish.bak'),
        })

        self.assertEqual(owned, self.config_dir / 'fish.bak')

    def test_no_backup_record_owns_nothing(self):
        dest = self.config_dir / 'fish'
        (self.config_dir / 'fish.bak').mkdir()

        self.assertIsNone(
            uninstall.owned_backup({'dest': dest, 'backup_created': False})
        )
        self.assertIsNone(
            uninstall.owned_backup({'dest': dest, 'backup_created': None})
        )


class TestLegacyStateRestoration(DotfilesTestCase):
    """Version 1.0 records still restore via filename discovery."""

    def test_legacy_backup_created_record_restores_newest_backup(self):
        source = self.dotfiles_dir / 'fish'
        source.mkdir()
        dest = self.config_dir / 'fish'
        dest.symlink_to(source)
        newest = self.config_dir / 'fish.bak.1'
        newest.mkdir()
        (newest / 'marker').write_text('newest')
        (self.config_dir / 'fish.bak').mkdir()

        state_file = Path(self.test_dir) / '.dotfiles-state'
        state_file.write_text(json.dumps({'version': '1.0', 'installed': [{
            'type': 'dir',
            'source': 'fish',
            'destination': str(dest),
            'backup_created': True,
        }]}))

        with mock.patch.object(uninstall, 'get_dotfiles_dir', return_value=self.dotfiles_dir), \
             mock.patch.object(sys, 'argv', ['uninstall.py', '--force']), \
             mock.patch.dict(os.environ, {'DOTFILES_STATE_FILE': str(state_file)}), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                uninstall.main()
        self.assertEqual(raised.exception.code, 0)

        self.assertEqual((dest / 'marker').read_text(), 'newest')


class TestMissingRecordedBackupWarns(DotfilesTestCase):
    """A recorded backup that vanished is louder than one that never existed."""

    def test_warns_when_recorded_backup_is_gone(self):
        dest = self.config_dir / 'fish'
        missing = self.config_dir / 'fish.bak'
        logger = Logger(verbose=False)

        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            restored = uninstall.restore_item_backup(
                {
                    'dest': dest,
                    'backup_created': True,
                    'backup_path': str(missing),
                },
                dry_run=False,
                logger=logger,
            )

        self.assertFalse(restored)
        self.assertIn(str(missing), out.getvalue())

    def test_silent_when_record_never_had_a_backup(self):
        dest = self.config_dir / 'fish'
        logger = Logger(verbose=False)

        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            restored = uninstall.restore_item_backup(
                {'dest': dest, 'backup_created': False},
                dry_run=False,
                logger=logger,
            )

        self.assertFalse(restored)
        self.assertEqual(out.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
