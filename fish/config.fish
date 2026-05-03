if status is-interactive
    # Commands to run in interactive sessions can go here
end

if command -v brew &>/dev/null
    set -l brew_prefix (brew --prefix)
    if test -d "$brew_prefix/share/fish/completions"
        set -p fish_complete_path "$brew_prefix/share/fish/completions"
    end
    if test -d "$brew_prefix/share/fish/vendor_completions.d"
        set -p fish_complete_path "$brew_prefix/share/fish/vendor_completions.d"
    end
end

if test -d /opt/homebrew
    set -l cppflags "-I/opt/homebrew/include"
    set -l ldflags "-L/opt/homebrew/lib"
    set -l pkg_paths "/opt/homebrew/lib/pkgconfig"

    # Add keg-only deps that native extensions commonly need
    for keg in icu4c openssl@3 readline libyaml libffi zlib
        set -l keg_prefix (find /opt/homebrew/opt -maxdepth 1 -name "$keg*" -type l | head -1)
        if test -n "$keg_prefix"
            test -d "$keg_prefix/include"; and set cppflags $cppflags "-I$keg_prefix/include"
            test -d "$keg_prefix/lib"; and set ldflags $ldflags "-L$keg_prefix/lib"
            test -d "$keg_prefix/lib/pkgconfig"; and set pkg_paths $pkg_paths "$keg_prefix/lib/pkgconfig"
        end
    end

    set -gx CPPFLAGS (string join -- " " $cppflags)
    set -gx LDFLAGS (string join -- " " $ldflags)
    set -gx PKG_CONFIG_PATH (string join -- ":" $pkg_paths)
end

# Add ~/.local/bin to PATH if it exists
if test -d "$HOME/.local/bin"
    fish_add_path "$HOME/.local/bin"
end

# Color scheme - Tokyo Night
set -g fish_color_autosuggestion 565f89
set -g fish_color_cancel --reverse
set -g fish_color_command 7aa2f7
set -g fish_color_comment 565f89
set -g fish_color_cwd 7aa2f7
set -g fish_color_cwd_root e0af68
set -g fish_color_end 9ece6a
set -g fish_color_error f7768e
set -g fish_color_escape 89ddff
set -g fish_color_history_current --bold
set -g fish_color_host 9ece6a
set -g fish_color_match --background=3b4261
set -g fish_color_normal c0caf5
set -g fish_color_operator 89ddff
set -g fish_color_param bb9af7
set -g fish_color_quote e0af68
set -g fish_color_redirection 7dcfff
set -g fish_color_search_match e0af68 --background=3b4261
set -g fish_color_selection c0caf5 --bold --background=3b4261
set -g fish_color_status f7768e
set -g fish_color_user 9ece6a
set -g fish_color_valid_path --underline
set -g fish_pager_color_completion c0caf5
set -g fish_pager_color_description 565f89
set -g fish_pager_color_prefix 7aa2f7 --bold --underline
set -g fish_pager_color_progress c0caf5 --background=3b4261
set -g fish_pager_color_selected_background --background=3b4261

set -gx EDITOR nvim
set -gx SSH_AUTH_SOCK "$HOME/.ssh/proton-pass-agent.sock"
set -gx GPG_TTY (tty)

abbr vi 'nvim'
abbr vim 'nvim'
abbr ll 'ls -ahl'

# Source local machine-specific config if it exists
if test -f ~/.config/fish/config.local.fish
    source ~/.config/fish/config.local.fish
end
