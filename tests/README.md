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
python3 tests/test_common.py
```

Run specific test class:
```bash
python3 -m unittest tests.test_install.TestFreshInstall -v
```

## Test Coverage

### Common library tests (`test_common.py`)

- **TestPromptUser** — `--force` short-circuit; y/n parsing with case + whitespace; reprompt on invalid input
- **TestStateManagerClear** — `.dotfiles-state` removal; no-op when missing
- **TestStateManagerMalformedJson** — graceful empty-state fallback for corrupt or missing-key JSON
- **TestStateManagerEnvOverride** — `DOTFILES_STATE_FILE` env var honored; explicit constructor arg wins over env
- **TestStateManagerDedup** — duplicate destinations merge to the latest entry on save
- **TestGetDotfilesDir** — returns absolute path to repo root
- **TestCreateSymlinkFailures** — missing source returns false; parent dirs created on demand; dry-run is a true no-op (returns success without creating parents or symlinks)
- **TestRemoveSymlinkSafety** — refuses non-symlinks and symlinks pointing outside the dotfiles dir; dry-run no-op
- **TestIsManagedSymlinkEdgeCases** — relative + absolute symlinks into the dotfiles dir are recognized; sibling-prefix directories (e.g. `dotfiles-old`) are *not* matched; non-symlinks return false

### Installation tests (`test_install.py`)

- **TestFreshInstall** — symlink creation when no config exists; no backup on fresh install; managed-symlink recognition
- **TestInstallWithExistingConfigs** — backup created for existing directories; numbered backups when `.bak` already exists
- **TestRestoreBackupNumbered** — backup restoration picks the highest-numbered backup; falls back to `.bak` when no numbered backups exist
- **TestZellijSpecialHandling** — `config.kdl` is generated from `config.shared.kdl`, regenerated on every run, and appends `config.local.kdl` when present; missing shared file or missing dir is a no-op; dry-run does not write
- **TestIdempotency** — already-installed symlinks are detected and skipped
- **TestStatePreservation** — existing state file is loaded before save; empty state works
- **TestFixSSHPermissions** — `~/.ssh` directory chmod 700, files chmod 600, no-op when already correct, follows symlinks to the repo, dry-run does not change perms, missing SSH dir is a no-op
- **TestProcessItem** — fresh install of dirs/files; error on missing source; type-mismatch detection; already-installed skip; existing-directory backup; stale managed symlink is relinked instead of erroring; broken symlinks are replaced; dry-run does not create symlinks
- **TestInstallBrewfile** — `--skip-brew` and `DOTFILES_SKIP_BREW` short-circuits; missing Brewfile and missing `brew` binary are silent no-ops; satisfied Brewfile skips install; dry-run with unsatisfied Brewfile does not install

### Uninstallation tests (`test_uninstall.py`)

- **TestUninstallWithBackups** — managed symlinks are removed and backups restored
- **TestUninstallFreshMachine** — uninstall works when no backup exists
- **TestMachineSpecificFilePreservation** — `fish/config.local.fish` and `zellij/config.kdl` are preserved across uninstall (with and without backup restoration); preservation handles missing local files; dry-run does not copy
- **TestDryRunMode** — backup dry-run makes no filesystem changes
- **TestRemoveSymlinkRefusesExternal** — symlinks pointing outside the dotfiles dir are not removed
- **TestRestoreBackupMissing** — restore returns false when no backup exists; dry-run preserves that signal

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
