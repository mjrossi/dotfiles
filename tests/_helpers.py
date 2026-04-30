"""Shared test fixtures for install/uninstall unit tests."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Let tests import `install`, `uninstall`, and `lib.common` from the repo root.
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.common import Logger


class DotfilesTestCase(unittest.TestCase):
    """Base class that stages a temp `dotfiles_dir` + fake HOME + ~/.config."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dotfiles_dir = Path(self.test_dir) / "dotfiles"
        self.home_dir = Path(self.test_dir) / "home"
        self.config_dir = self.home_dir / ".config"
        for p in (self.dotfiles_dir, self.home_dir, self.config_dir):
            p.mkdir()
        self.logger = Logger(verbose=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
