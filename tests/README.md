# Dotfiles Tests

Unit tests for the dotfiles installation and uninstallation scripts.

## Running Tests

Run all tests:
```bash
python3 -m unittest discover tests -v
```

Run specific test file:
```bash
python3 tests/test_install.py
python3 tests/test_uninstall.py
```

Run specific test class:
```bash
python3 -m unittest tests.test_install.TestFreshInstall -v
```

## Test Coverage

### Installation Tests (`test_install.py`)

**TestFreshInstall** - Fresh machine with no existing configs
- ✓ Symlink creation when no config exists
- ✓ No backup created on fresh install
- ✓ Managed symlinks are recognized

**TestInstallWithExistingConfigs** - Existing configs present
- ✓ Backup created for existing directory
- ✓ Backup numbering when .bak already exists

**TestZellijSpecialHandling** - Zellij config.kdl creation
- ✓ config.kdl created from config.shared.kdl
- ✓ Existing config.kdl not overwritten

**TestIdempotency** - Multiple install runs
- ✓ Already installed symlinks detected and skipped

### Uninstallation Tests (`test_uninstall.py`)

**TestUninstallWithBackups** - Uninstall with backups present
- ✓ Managed symlinks are removed
- ✓ Backups are restored after removal

**TestUninstallFreshMachine** - Uninstall without backups
- ✓ Uninstall works when no backup exists

**TestMachineSpecificFilePreservation** - Preserve local configs
- ✓ fish/config.local.fish is preserved
- ✓ zellij/config.kdl is preserved
- ✓ File preservation works with backup restoration

**TestDryRunMode** - Dry-run doesn't modify filesystem
- ✓ Backup dry-run makes no changes

## Test Structure

Tests use Python's built-in `unittest` framework with temporary directories for isolation:

```python
def setUp(self):
    """Create temporary test environment."""
    self.test_dir = tempfile.mkdtemp()
    # Create test files...

def tearDown(self):
    """Clean up temporary files."""
    shutil.rmtree(self.test_dir)
```

Each test is isolated and doesn't affect the actual filesystem or dotfiles.
