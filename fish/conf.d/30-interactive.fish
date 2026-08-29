# Interactive-only setup. Colours, abbreviations and GPG_TTY mean nothing to a
# script, and `tty` is a process spawn, so none of this should run for
# `fish -c`. Previously all of it sat outside the interactive guard while the
# guard itself was empty.
status is-interactive; or exit

set -g fish_greeting ""

# GPG needs to know which terminal to prompt on; only meaningful with one.
set -gx GPG_TTY (tty)

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

abbr vi 'nvim'
abbr vim 'nvim'
abbr ll 'ls -ahl'
