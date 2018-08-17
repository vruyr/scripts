#!/usr/bin/env bash

if ! [ "${BASH_VERSINFO[0]}" -ge 3 -a "${BASH_VERSINFO[1]}" -ge 2 -a "${BASH_VERSINFO[2]}" -ge 57 ]; then
	echo "FATAL: Unsupported bash version: $(declare -p BASH_VERSINFO 2>&1)" >&2
	exit 127
fi


function main() {
	echo --- Homebrew Update
	eval_indent 'brew update'
	echo --- Homebrew Outdated
	eval_indent 'brew outdated --verbose'
	echo --- Homebrew Cask Outdated
	eval_indent 'brew cask outdated --verbose --greedy'
	if [ -n "$PYV_ROOT_DIR" ]; then
		echo --- pyv
		eval_indent 'show_pyv_updates "$PYV_ROOT_DIR"'
	fi
	echo --- Mac App Store
	eval_indent 'softwareupdate --list'
	echo ...
}


function show_pyv_updates() {
	rootdir="$1"
	for venv in $(compgen -A directory "$PYV_ROOT_DIR/"); do
		echo "--- $venv"
		eval_indent '$venv/bin/pip list --outdated --format=json | jq -r '\''.[]|.name + "==" + .version + " < " + .latest_version'\'
	done
}


function eval_indent() {
	eval "$@" 2>&1 | sed 's/^/'$'\t''/'
}


if ! $(return >/dev/null 2>&1); then
	main "$@"
fi
