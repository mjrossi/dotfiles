# Environment needed by non-interactive shells too (scripts, `fish -c`,
# anything an editor or launchd spawns), so deliberately not guarded by
# `status is-interactive`.
set -gx EDITOR nvim
set -gx SSH_AUTH_SOCK "$HOME/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
