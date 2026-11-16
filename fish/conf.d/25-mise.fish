# mise, split by shell type, which is mise's own recommended setup.
#
# Homebrew's mise ships /opt/homebrew/share/fish/vendor_conf.d/mise-activate.fish,
# which runs `mise activate fish | source` in every fish process unless
# MISE_FISH_AUTO_ACTIVATE is "0". That activation (`mise activate` plus the
# first `hook-env`) was ~66 of the ~70ms each shell took to start, and
# non-interactive shells paid it too -- every `fish -c`, every `:!` and
# vim.fn.system() from Neovim. Fish sources all of the user's conf.d before
# any vendor_conf.d, so setting the variable here always beats that snippet.
# It is set global rather than exported, so it only affects this process;
# child shells read this file again and make their own choice.
#
#   interactive      full activation: PATH plus mise [env] values, updated on
#                    every prompt and directory change.
#   non-interactive  just the shims directory on PATH. Tools still resolve to
#                    the version mise would pick for the current directory,
#                    but mise [env] values (MISE_ENV and the like) are not set
#                    unless inherited from an activated parent shell.
#
# Runs after 10-paths.fish, so mise's paths land ahead of ~/.local/bin and
# Homebrew either way.
set -g MISE_FISH_AUTO_ACTIVATE 0

if status is-interactive
    if command -q mise
        mise activate fish | source
    end
else
    fish_add_path --global --path $HOME/.local/share/mise/shims
end
