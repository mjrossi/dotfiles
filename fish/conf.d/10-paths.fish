# Ordered after 00-homebrew.fish on purpose. Both prepend, so going last puts
# ~/.local/bin ahead of /opt/homebrew/bin: a binary you drop here by hand beats
# the packaged one, which is what every other Unix does and what you almost
# certainly meant by putting it there. mise still shadows both, so this does
# not undercut the mise-then-brew policy in CLAUDE.md.
#
# (The previous config had the opposite order, but by accident rather than
# intent: ~/.local/bin was coming from a universal fish_user_paths applied
# before config.fish ran, which made config.fish's own fish_add_path a no-op.)
#
# --global, not the default universal: a universal fish_user_paths is written
# into fish_variables and then applies forever regardless of what this repo
# says, which makes the real PATH configuration invisible. Keeping it global
# means this file is the only thing that puts ~/.local/bin on PATH.
if test -d $HOME/.local/bin
    fish_add_path --global $HOME/.local/bin
end
