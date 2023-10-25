## .zshrc - Loaded after .zshenv
## Script relies heavily on safepathappend, safepathprepend and safesource from .zshenv

## Environment display setup
autoload -U compinit
compinit

autoload -U colors
colors

autoload -U select-word-style
select-word-style bash

bindkey -e

setopt prompt_subst

# Environment diagnostic data
export LOCALE="en_US.UTF-8"
export LANG="en_US.UTF-8"

platform='unknown'
unamestr=`uname`
if [[ "$unamestr" == 'Linux' ]]; then
   platform='linux'
elif [[ "$unamestr" == 'FreeBSD' ]]; then
   platform='freebsd'
elif [[ "$unamestr" == 'Darwin' ]]; then
   platform='osx'
fi

#Prompt Setup
export CLICOLOR=1
export LSCOLORS=GxFxCxDxBxegedabagaced
export LS_COLORS="di=34:ln=35:so=32:pi=33:ex=31:bd=34:cd=34:su=0:sg=0:tw=0:ow=0:"
export GREP_OPTIONS='--color'
export EDITOR=vim
export LESS='XFR'

if [[ "$platform" == "osx" ]]; then
  PROMPT='%{$fg_bold[green]%}%m: %{$fg_bold[magenta]%}[%{$(free)]%} %{$fg_bold[blue]%}%~%{$fg_bold[green]%}$(git_prompt_info)%{$reset_color%} %#
→ '
else
  PROMPT='%{$fg_bold[green]%}%m: %{$fg_bold[magenta]%}%{$fg_bold[blue]%}%~%{$fg_bold[green]%}$(git_prompt_info)%{$reset_color%} %#
→ '
fi

# ZSH Settings (LOCAL)
## The local version of this file
safesource "$HOME/.zshrc.local"

# Alias definitions (CORE)
## Aliases tend to be long and complicated so they exist elsewhere!
safesource "$HOME/.aliases_shared"
safesource "$HOME/.zsh_aliases"
## (LOCAL)
safesource $HOME/.aliases_shared.local
safesource $HOME/.zsh_aliases.local

# Script Directory (CORE)
safepathprepend $HOME/.bin
## Local (LOCAL)
safepathprepend $HOME/.bin.local

export GPG_TTY=$(tty)

# Perforce
export P4USER=matthew.rossi
export P4PORT=ssl:p4proxy.ashburn.soma.salesforce.com:1999

# asdf
safesource $HOME/.asdf/asdf.sh
#safesource /usr/local/opt/asdf/libexec/asdf.sh

# direnv
eval "$(asdf exec direnv hook zsh)"

# pyenv
export VIRTUALENVWRAPPER_PYTHON=/Users/matthew.rossi/.pyenv/shims/python
# export VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python3
if command -v pyenv 1>/dev/null 2>&1; then
  eval "$(pyenv init -)"
fi
source /usr/local/bin/virtualenvwrapper.sh

#Common Tools

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

source "${XDG_CONFIG_HOME:-$HOME/.config}/asdf-direnv/zshrc"
