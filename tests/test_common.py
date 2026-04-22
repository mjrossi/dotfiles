#!/usr/bin/env python3
"""
Unit tests for lib/common.py shared helpers.
"""

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.common import (
    Logger, StateManager,
    create_symlink, get_dotfiles_dir, is_managed_symlink,
    prompt_user, remove_symlink,
)


class TestPromptUser(unittest.TestCase):
    """prompt_user handles force flag, input parsing, and reprompts."""

    def test_force_returns_true_without_prompting(self):
        with mock.patch('builtins.input') as mock_input:
            self.assertTrue(prompt_user("continue?", force=True))
            mock_input.assert_not_called()

    def test_accepts_y_yes_case_and_whitespace(self):
        for response in ('y', 'Y', 'yes', 'YES', '  yes  ', ' y\n'):
            with mock.patch('builtins.input', return_value=response):
                self.assertTrue(prompt_user("continue?"), f"failed on {response!r}")

    def test_accepts_n_no_case_and_whitespace(self):
        for response in ('n', 'N', 'no', 'NO', '  no  '):
            with mock.patch('builtins.input', return_value=response):
                self.assertFalse(prompt_user("continue?"), f"failed on {response!r}")

    def test_reprompts_on_invalid_input(self):
        responses = iter(['maybe', '', 'huh?', 'y'])
        with mock.patch('builtins.input', side_effect=lambda _: next(responses)):
            # Swallow the "Please answer 'y' or 'n'" reprompt noise
            with redirect_stderr(io.StringIO()), mock.patch('sys.stdout', new=io.StringIO()):
                self.assertTrue(prompt_user("continue?"))


class TestStateManagerClear(unittest.TestCase):
    """StateManager.clear removes the state file idempotently."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.state_file = Path(self.test_dir) / ".dotfiles-state"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_clear_removes_existing_state_file(self):
        state = StateManager(state_file=self.state_file)
        state.add('dir', 'fish', Path('/home/.config/fish'), backup_created=False)
        state.save()
        self.assertTrue(self.state_file.exists())

        state.clear()

        self.assertFalse(self.state_file.exists())

    def test_clear_is_noop_when_state_file_missing(self):
        state = StateManager(state_file=self.state_file)
        self.assertFalse(self.state_file.exists())

        state.clear()

        self.assertFalse(self.state_file.exists())


class TestStateManagerMalformedJson(unittest.TestCase):
    """StateManager.load tolerates corrupt / unexpected state files."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.state_file = Path(self.test_dir) / ".dotfiles-state"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_returns_empty_on_corrupt_json(self):
        self.state_file.write_text("{not json at all")

        state = StateManager(state_file=self.state_file)
        with redirect_stderr(io.StringIO()) as captured:
            records = state.load()

        self.assertEqual(records, [])
        self.assertIn("Could not parse state file", captured.getvalue())

    def test_load_returns_empty_when_installed_key_missing(self):
        self.state_file.write_text(json.dumps({'version': '1.0'}))

        state = StateManager(state_file=self.state_file)
        records = state.load()

        self.assertEqual(records, [])


class TestStateManagerDedup(unittest.TestCase):
    """StateManager.save deduplicates records by destination, newest wins."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.state_file = Path(self.test_dir) / ".dotfiles-state"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_duplicate_destinations_are_merged_keeping_latest(self):
        state = StateManager(state_file=self.state_file)
        dest = Path('/home/.config/fish')
        state.add('dir', 'fish', dest, backup_created=False)
        state.add('dir', 'fish', dest, backup_created=True)
        state.save()

        records = StateManager(state_file=self.state_file).load()

        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]['backup_created'])


class TestGetDotfilesDir(unittest.TestCase):
    """get_dotfiles_dir resolves to an absolute path at the repo root."""

    def test_returns_absolute_path_to_repo_root(self):
        result = get_dotfiles_dir()

        self.assertTrue(result.is_absolute())
        self.assertTrue((result / 'lib' / 'common.py').exists())


class TestCreateSymlinkFailures(unittest.TestCase):
    """create_symlink validates inputs and handles dry-run."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)
        self.logger = Logger(verbose=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_returns_false_when_source_missing(self):
        source = self.root / "does-not-exist"
        dest = self.root / "dest"

        with redirect_stderr(io.StringIO()):
            result = create_symlink(source, dest, dry_run=False, logger=self.logger)

        self.assertFalse(result)
        self.assertFalse(dest.exists())
        self.assertFalse(dest.is_symlink())

    def test_creates_parent_directories_as_needed(self):
        source = self.root / "source"
        source.mkdir()
        dest = self.root / "nested" / "deeper" / "dest"

        result = create_symlink(source, dest, dry_run=False, logger=self.logger)

        self.assertTrue(result)
        self.assertTrue(dest.is_symlink())
        self.assertTrue(dest.parent.is_dir())

    def test_dry_run_returns_true_without_creating_symlink(self):
        source = self.root / "source"
        source.mkdir()
        dest = self.root / "dest"

        result = create_symlink(source, dest, dry_run=True, logger=self.logger)

        self.assertTrue(result)
        self.assertFalse(dest.exists())
        self.assertFalse(dest.is_symlink())


class TestRemoveSymlinkSafety(unittest.TestCase):
    """remove_symlink refuses non-symlinks and links outside dotfiles_dir."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)
        self.dotfiles_dir = self.root / "dotfiles"
        self.dotfiles_dir.mkdir()
        self.outside_dir = self.root / "outside"
        self.outside_dir.mkdir()
        self.logger = Logger(verbose=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_refuses_non_symlink(self):
        regular = self.root / "regular"
        regular.mkdir()

        with redirect_stderr(io.StringIO()):
            result = remove_symlink(regular, self.dotfiles_dir,
                                    dry_run=False, logger=self.logger)

        self.assertFalse(result)
        self.assertTrue(regular.exists())

    def test_refuses_symlink_pointing_outside_dotfiles(self):
        link = self.root / "link"
        link.symlink_to(self.outside_dir)

        with redirect_stderr(io.StringIO()):
            result = remove_symlink(link, self.dotfiles_dir,
                                    dry_run=False, logger=self.logger)

        self.assertFalse(result)
        self.assertTrue(link.is_symlink())

    def test_dry_run_returns_true_without_removing(self):
        target = self.dotfiles_dir / "item"
        target.mkdir()
        link = self.root / "link"
        link.symlink_to(target)

        result = remove_symlink(link, self.dotfiles_dir,
                                dry_run=True, logger=self.logger)

        self.assertTrue(result)
        self.assertTrue(link.is_symlink())


class TestIsManagedSymlinkEdgeCases(unittest.TestCase):
    """is_managed_symlink handles relative targets and non-symlink inputs."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir).resolve()
        self.dotfiles_dir = self.root / "dotfiles"
        self.dotfiles_dir.mkdir()
        (self.dotfiles_dir / "fish").mkdir()
        self.outside_dir = self.root / "outside"
        self.outside_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_relative_symlink_into_dotfiles_is_managed(self):
        link = self.root / "fish-link"
        # Relative target: ../dotfiles/fish from self.root
        link.symlink_to(Path("dotfiles") / "fish")

        self.assertTrue(is_managed_symlink(link, self.dotfiles_dir))

    def test_symlink_outside_dotfiles_is_not_managed(self):
        link = self.root / "outside-link"
        link.symlink_to(self.outside_dir)

        self.assertFalse(is_managed_symlink(link, self.dotfiles_dir))

    def test_regular_file_is_not_managed(self):
        regular = self.root / "regular.txt"
        regular.write_text("hello")

        self.assertFalse(is_managed_symlink(regular, self.dotfiles_dir))

    def test_regular_directory_is_not_managed(self):
        regular = self.root / "regular-dir"
        regular.mkdir()

        self.assertFalse(is_managed_symlink(regular, self.dotfiles_dir))


if __name__ == '__main__':
    unittest.main()
