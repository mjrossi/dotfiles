# Startup configuration lives in conf.d/, which fish sources before this file,
# sorted by filename:
#
#   00-homebrew.fish     Homebrew env (static; see the note in that file)
#   10-paths.fish        ~/.local/bin, deliberately ahead of Homebrew
#   20-env.fish          EDITOR, SSH_AUTH_SOCK -- non-interactive shells too
#   30-interactive.fish  colours, abbreviations, GPG_TTY
#
# What is left here is the machine-specific include, which has to run last so
# it can override anything above.

if test -f ~/.config/fish/config.local.fish
    source ~/.config/fish/config.local.fish
end
