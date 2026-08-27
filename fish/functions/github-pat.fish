# Read the 'github-pat-claude-mcp' item from Proton Pass into this shell.
#
# On demand, not on startup: this is a vault-item read, which needs the
# `ProtonPassCLI` key in the login keychain. Running it from a fish_prompt
# hook meant macOS asked to authorize keychain access on every new shell.
#
# The GitHub MCP server reads GITHUB_PERSONAL_ACCESS_TOKEN from its
# environment at launch, so run this before starting a session that needs
# it (or call it from ~/.config/fish/config.local.fish on a machine where
# you always want it).
function github-pat --description 'Load GITHUB_PERSONAL_ACCESS_TOKEN from Proton Pass'
    if not command -q pass-cli
        echo "github-pat: pass-cli is not installed" >&2
        return 1
    end
    set -l share "AAxj8oq3KJbZiYmPYPQQSILmkQNboq5IK62XMGI8uYVOGKKxibbx0dWyGArzM6fNPqgk9XGgEoYkggOxMa0JlA=="
    set -l item "NPu8AGXPB9P_aeNO9-gK2ZwQSVsmKnEBPSKcp4Q2Rv4CnQHQw6EM5tcqt-rNWqj-Nl2LdPRvVBgSSB11D3Ugpg=="
    set -l pat (pass-cli item view --share-id $share --item-id $item --field "API Key" --output human 2>/dev/null)
    if test -z "$pat"
        echo "github-pat: could not read the token from Proton Pass" >&2
        return 1
    end
    set -gx GITHUB_PERSONAL_ACCESS_TOKEN $pat
end
