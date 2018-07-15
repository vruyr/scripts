#!/usr/bin/env bash

if ! [ "${BASH_VERSINFO[0]}" -ge 3 -a "${BASH_VERSINFO[1]}" -ge 2 -a "${BASH_VERSINFO[2]}" -ge 57 ]; then
	echo "FATAL: Unsupported bash version: $(declare -p BASH_VERSINFO 2>&1)" >&2
	exit 127
fi


function main() {
	echo --- Homebrew Update
	exec_indent brew update
	echo --- Homebrew Outdated
	exec_indent brew outdated --verbose
	echo --- Homebrew Cask Outdated
	exec_indent brew cask outdated --verbose --greedy
	echo --- Mac App Store
	exec_indent softwareupdate --list
	if [ -n "$PYV_ROOT_DIR" ]; then
		echo --- pyv
		exec_indent show_pyv_updates "$PYV_ROOT_DIR"
	fi
	echo ...
}


function show_pyv_updates() {
	rootdir="$1"
	for venv in $(compgen -A directory "$PYV_ROOT_DIR/"); do
		echo "--- $venv"
		exec_indent $venv/bin/pip list --outdated
	done
}


function exec_indent() {
	"$@" 2>&1 | sed 's/^/'$'\t''/'
}


if ! $(return >/dev/null 2>&1); then
	main "$@"
fi
