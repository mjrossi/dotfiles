if status is-interactive
    # Commands to run in interactive sessions can go here
end

if test -d (brew --prefix)"/share/fish/completions"
    set -p fish_complete_path (brew --prefix)/share/fish/completions
end

if test -d (brew --prefix)"/share/fish/vendor_completions.d"
    set -p fish_complete_path (brew --prefix)/share/fish/vendor_completions.d
end

if test -d "/opt/homebrew"
  set -gx CPPFLAGS "-I /opt/homebrew/include -I /opt/homebrew/opt/icu4c/include"
  set -gx LDFLAGS "-L /opt/homebrew/lib -L /opt/homebrew/opt/icu4c/lib"
  set -gx PKG_CONFIG_PATH "/opt/homebrew/lib/pkgconfig:/opt/homebrew/opt/icu4c/lib/pkgconfig"
end

# Add ~/.local/bin to PATH if it exists
if test -d "$HOME/.local/bin"
    fish_add_path "$HOME/.local/bin"
end

# Color scheme - Dracula-inspired
set -g fish_color_autosuggestion BD93F9
set -g fish_color_cancel --reverse
set -g fish_color_command F8F8F2
set -g fish_color_comment 6272A4
set -g fish_color_cwd green
set -g fish_color_cwd_root red
set -g fish_color_end 50FA7B
set -g fish_color_error FFB86C
set -g fish_color_escape 00a6b2
set -g fish_color_history_current --bold
set -g fish_color_host normal
set -g fish_color_match --background=brblue
set -g fish_color_normal normal
set -g fish_color_operator 00a6b2
set -g fish_color_param FF79C6
set -g fish_color_quote F1FA8C
set -g fish_color_redirection 8BE9FD
set -g fish_color_search_match bryellow --background=brblack
set -g fish_color_selection white --bold --background=brblack
set -g fish_color_status red
set -g fish_color_user brgreen
set -g fish_color_valid_path --underline
set -g fish_pager_color_completion normal
set -g fish_pager_color_description B3A06D
set -g fish_pager_color_prefix normal --bold --underline
set -g fish_pager_color_progress brwhite --background=cyan
set -g fish_pager_color_selected_background --background=brblack

set -gx EDITOR nvim
set -gx SSH_AUTH_SOCK "~/Library/Group\ Containers/2BUA8C4S2C.com.1password/t/agent.soc"
set -gx GPG_TTY (tty)

abbr h 'heroku'
abbr vi 'nvim'
abbr vim 'nvim'
abbr ll 'ls -ahl'

# Source local machine-specific config if it exists
if test -f ~/.config/fish/config.local.fish
    source ~/.config/fish/config.local.fish
end
