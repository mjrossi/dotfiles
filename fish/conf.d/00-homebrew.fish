# Homebrew environment, transcribed from `brew shellenv fish`.
#
# Inlined rather than shelled out to: `brew shellenv` is a bash script that
# cost ~21ms on every shell start, interactive or not, to print output that is
# constant for a given install prefix. Regenerate with `brew shellenv fish` if
# Homebrew ever changes what it exports.
#
# Runs before mise's vendor snippet (/opt/homebrew/share/fish/vendor_conf.d/
# mise-activate.fish), which is the ordering that matters upward: mise prepends
# its shims on top of everything here, so mise-managed tools always win.
#
# It also runs before 10-paths.fish, which is what puts ~/.local/bin ahead of
# these -- see that file.

if test -d /opt/homebrew
    set --global --export HOMEBREW_PREFIX /opt/homebrew
    set --global --export HOMEBREW_CELLAR /opt/homebrew/Cellar
    set --global --export HOMEBREW_REPOSITORY /opt/homebrew

    fish_add_path --global --move --path /opt/homebrew/bin /opt/homebrew/sbin

    if test -n "$MANPATH[1]"
        set --global --export MANPATH '' $MANPATH
    end

    if not set --query INFOPATH
        set INFOPATH ''
    end
    if not contains /opt/homebrew/share/info $INFOPATH
        set --global --export INFOPATH /opt/homebrew/share/info $INFOPATH
    end
end
