# Claude Code skills

Personal skills for Claude Code. `install.py` links each directory here to
`~/.claude/skills/<name>` (the `CLAUDE_SKILLS` tuple in `lib/common.py`).

## Origin

All sixteen are unmodified copies from
[mickeyyaya/refactoring-skills-claude-code](https://github.com/mickeyyaya/refactoring-skills-claude-code)
at commit `cd0c227` (2026-03-17), MIT licensed; see [LICENSE](./LICENSE).
Upstream ships 76 skills. These are the ones that have actually been used;
loading all of them pushed Claude's skill listing over its size budget, so
descriptions were being dropped.

They are vendored rather than tracked because upstream is small and quiet.
Edit them here freely. To pick up an upstream change, copy the skill
directory over and review the diff.

## Adding or removing a skill

Add or delete the directory, update `CLAUDE_SKILLS` in `lib/common.py`, and
re-run `./install.py`. If `~/.claude/skills/<name>` already exists as a real
directory, remove it first: the installer would otherwise back it up to
`<name>.bak` next to it, and Claude would load that backup as a second skill.

## Not managed here

- `~/.claude/skills/code-review-skill` is a git clone of
  [awesome-skills/code-review-skill](https://github.com/awesome-skills/code-review-skill),
  which is actively maintained. `just claude-review-skill` clones it or
  fast-forwards it.
- `~/.claude/skills/synced/` is written by Claude from the claude.ai account.
- Plugin skills (superpowers and others) are installed with `claude plugin`.
