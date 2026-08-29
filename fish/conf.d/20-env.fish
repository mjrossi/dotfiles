# Environment needed by non-interactive shells too (scripts, `fish -c`,
# anything an editor or launchd spawns), so deliberately not guarded by
# `status is-interactive`.
set -gx EDITOR nvim
set -gx SSH_AUTH_SOCK "$HOME/.ssh/proton-pass-agent.sock"
