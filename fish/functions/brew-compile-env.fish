function brew-compile-env --description 'Export CPPFLAGS/LDFLAGS/PKG_CONFIG_PATH for keg-only Homebrew deps'
    # Building native extensions (gem install, pip install of anything with a C
    # extension) needs headers and libraries from keg-only formulae, which
    # Homebrew deliberately keeps off the default search paths.
    #
    # This used to run on every shell start, where it cost ~12ms in `find`
    # calls to set three variables that only matter while compiling. Run it
    # first if a build cannot find headers.
    if not test -d /opt/homebrew
        echo "brew-compile-env: no /opt/homebrew on this machine" >&2
        return 1
    end

    set -l cppflags "-I/opt/homebrew/include"
    set -l ldflags "-L/opt/homebrew/lib"
    set -l pkg_paths "/opt/homebrew/lib/pkgconfig"

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
