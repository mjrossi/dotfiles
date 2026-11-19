brew "mise"
brew "fish"

# 1Password CLI. Cask rather than mise: `op` talks to the desktop app over a
# local socket for biometric unlock and SSH-agent integration, which is exactly
# the system-integration exception in the package policy.
cask "1password-cli"

# Ghostty, the terminal (config in ghostty/). A macOS app bundle, so a cask.
# On a machine where Ghostty.app was installed by hand, bring it under brew
# once with `brew install --cask --adopt ghostty`; otherwise `brew bundle`
# refuses to overwrite the existing app.
cask "ghostty"

# R from CRAN's official .pkg. Cask rather than mise: mise has no binary R
# backend (the asdf plugin compiles from source), and CRAN's prebuilt macOS
# packages -- sf with its bundled GDAL/PROJ/GEOS above all -- are built against
# CRAN's R.framework. The `r` formula would force every one of those to build
# from source against Homebrew's GDAL. Symlinks R/Rscript into /usr/local/bin.
cask "r-app"

brew "gnupg"
brew "pinentry-mac"

# Trivial unix utilities with no mise registry entry. age and sigtop moved
# to mise (aqua:FiloSottile/age, go:github.com/tbvdm/sigtop/cmd/sigtop); the
# brew copies stay installed until removed by hand, since install.py never
# runs `brew bundle cleanup`.
brew "p7zip"
brew "rename"
brew "telnet"
brew "wget"
brew "wimlib"
