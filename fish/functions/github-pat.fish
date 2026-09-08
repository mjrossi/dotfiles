# Read the 'github-pat-claude-mcp' item from 1Password into this shell.
#
# On demand, not on startup: `op read` round-trips through the 1Password
# desktop app and can raise a biometric prompt. Running it from a
# fish_prompt hook would ask for Touch ID on every new shell.
#
# The GitHub MCP server reads GITHUB_PERSONAL_ACCESS_TOKEN from its
# environment at launch, so run this before starting a session that needs
# it (or call it from ~/.config/fish/config.local.fish on a machine where
# you always want it).
function github-pat --description 'Load GITHUB_PERSONAL_ACCESS_TOKEN from 1Password'
    if not command -q op
        echo "github-pat: the 1Password CLI (op) is not installed" >&2
        return 1
    end
    # Vault is pinned: several items are duplicated into the legacy
    # "Old 1PW Private Vault", and Personal is the source of truth.
    set -l ref "op://Personal/github-pat-claude-mcp/API Key"
    set -l pat (op read $ref 2>/dev/null)
    if test $status -ne 0; or test -z "$pat"
        echo "github-pat: could not read $ref" >&2
        echo "github-pat: check that 1Password is unlocked, and that" >&2
        echo "            Settings -> Developer -> 'Integrate with 1Password CLI' is on" >&2
        return 1
    end
    set -gx GITHUB_PERSONAL_ACCESS_TOKEN $pat
end
