# Set GITHUB_TOKEN from gh CLI on first prompt, if gh is installed and logged in.
# Silently no-ops when gh is missing or unauthenticated.
function __mjr_load_github_token --on-event fish_prompt
    functions -e __mjr_load_github_token
    command -q gh; or return
    set -l token (gh auth token 2>/dev/null)
    test $status -eq 0 -a -n "$token"; and set -gx GITHUB_TOKEN $token
end
