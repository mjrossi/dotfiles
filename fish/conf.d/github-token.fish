# On first prompt: GITHUB_TOKEN from the gh CLI (for gh itself). Silently
# no-ops when gh is missing or unauthenticated.
#
# GITHUB_PERSONAL_ACCESS_TOKEN (consumed by the GitHub MCP server) is
# deliberately NOT loaded here -- see the `github-pat` function. Reading it
# from Proton Pass touches the login keychain, and doing that per shell
# made macOS prompt for keychain authorization on every new terminal.
function __mjr_load_github_token --on-event fish_prompt
    functions -e __mjr_load_github_token
    command -q gh; or return
    set -l token (gh auth token 2>/dev/null)
    test -n "$token"; and set -gx GITHUB_TOKEN $token
end
