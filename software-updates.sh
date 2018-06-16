#!/usr/bin/env bash

if ! [ "${BASH_VERSINFO[0]}" -ge 3 -a "${BASH_VERSINFO[1]}" -ge 2 -a "${BASH_VERSINFO[2]}" -ge 57 ]; then
	echo "FATAL: Unsupported bash version: $(declare -p BASH_VERSINFO 2>&1)" >&2
	exit 127
fi


function main() {
	echo --- Homebrew
	exec_indent brew outdated --verbose
	echo --- Homebrew Cask
	exec_indent brew cask outdated --verbose --greedy
	echo --- Mac App Store
	exec_indent softwareupdate --list
	echo ...
}


function exec_indent() {
	"$@" 2>&1 | sed 's/^/'$'\t''/'
}


if ! $(return >/dev/null 2>&1); then
	main "$@"
fi
