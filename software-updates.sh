#!/usr/bin/env bash

if ! [ "${BASH_VERSINFO[0]}" -ge 3 -a "${BASH_VERSINFO[1]}" -ge 2 -a "${BASH_VERSINFO[2]}" -ge 57 ]; then
	echo "FATAL: Unsupported bash version: $(declare -p BASH_VERSINFO 2>&1)" >&2
	exit 127
fi


function main() {
	if [ $# -eq 0 ]; then
		set -- --all
	fi

	local homebrew_outdated=
	local homebrew_cask_outdated=
	local pyv_outdated=
	local macappstore_outdated=

	while [ $# -gt 0 ]; do
		local opt="$1"
		shift
		case "$opt" in
			"--all")
				set -- --brew --brew-cask --pyv --macappstore "$@"
				;;
			"--brew")
				homebrew_outdated=1
				;;
			"--no-brew")
				homebrew_outdated=
				;;
			"--brew-cask")
				homebrew_cask_outdated=1
				;;
			"--no-brew-cask")
				homebrew_cask_outdated=
				;;
			"--pyv")
				pyv_outdated=1
				;;
			"--no-pyv")
				pyv_outdated=
				;;
			"--macappstore"|"--appstore")
				macappstore_outdated=1
				;;
			"--no-macappstore"|"--no-appstore")
				macappstore_outdated=
				;;
			*)
				echo "invalid parameter: $opt"
				return 1
				;;
		esac
	done

	if [ "$homebrew_outdated" -o "$homebrew_cask_outdated" ]; then
		echo "--- Homebrew Update"
		eval_indent 'brew update'
	fi
	if [ "$homebrew_outdated" ]; then
		echo "--- Homebrew Outdated"
		eval_indent 'brew outdated --verbose'
	fi
	if [ "$homebrew_cask_outdated" ]; then
		echo "--- Homebrew Cask Outdated"
		eval_indent 'brew cask outdated --verbose --greedy'
	fi
	if [ "$pyv_outdated" ]; then
		if [ -n "$PYV_ROOT_DIR" ]; then
			echo "--- pyv: $PYV_ROOT_DIR"
			eval_indent 'show_pyv_updates "$PYV_ROOT_DIR"'
		fi
	fi
	if [ "$macappstore_outdated" ]; then
		echo "--- Mac App Store"
		eval_indent 'softwareupdate --list'
	fi
	echo ...
}


function show_pyv_updates() {
	rootdir="$1"
	local output=
	for venv in $(compgen -A directory "$rootdir/"); do
		output="$(eval_indent '$venv/bin/pip list --outdated --format=json | jq -r '\''.[]|.name + "==" + .version + " < " + .latest_version'\')"
		if [ -z "$output" ]; then
			continue
		fi
		echo "--- ${venv#$rootdir/}"
		echo "$output"
	done
}


function eval_indent() {
	eval "$@" 2>&1 | sed 's/^/'$'\t''/'
}


if ! $(return >/dev/null 2>&1); then
	main "$@"
fi
