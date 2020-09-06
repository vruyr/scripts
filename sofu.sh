#!/usr/bin/env bash

if ! [ "${BASH_VERSINFO[0]}" -ge 3 -a "${BASH_VERSINFO[1]}" -ge 2 -a "${BASH_VERSINFO[2]}" -ge 57 ]; then
	echo "FATAL: Unsupported bash version: $(declare -p BASH_VERSINFO 2>&1)" >&2
	exit 127
fi


BREW_BUNDLE_FILE_PATH="$HOME/.config/homebrew/Brewfile"


function main() {
	if [ $# -eq 0 ]; then
		set -- --all
	fi

	local homebrew_bundle_check=
	local homebrew_outdated=
	local homebrew_cask_outdated=
	local homebrew_bundle_cleanup=
	local npm_outdated=
	local pyv_outdated=
	local macappstore_outdated=
	local macossystem_outdated=

	while [ $# -gt 0 ]; do
		local opt="$1"
		shift
		case "$opt" in
			"--all")
				set -- --brew-bundle-cleanup --brew-bundle-check --brew --brew-cask --npm --pyv --macappstore --macossystem "$@"
				;;
			"--brew-bundle-check")
				homebrew_bundle_check=1
				;;
			"--no-brew-bundle-check")
				homebrew_bundle_check=
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
			"--brew-bundle-cleanup")
				homebrew_bundle_cleanup=1
				;;
			"--no-brew-bundle-cleanup")
				homebrew_bundle_cleanup=
				;;
			"--npm")
				npm_outdated=1
				;;
			"--no-npm")
				npm_outdated=
				;;
			"--pyv")
				pyv_outdated=1
				;;
			"--no-pyv")
				pyv_outdated=
				;;
			"--macappstore"|"--mas")
				macappstore_outdated=1
				;;
			"--no-macappstore"|"--no-mas")
				macappstore_outdated=
				;;
			"--macossystem"|"--system"|"--sys")
				macossystem_outdated=1
				;;
			"--no-macossystem"|"--no-system"|"--no-sys")
				macossystem_outdated=
				;;
			*)
				echo "invalid parameter: $opt"
				return 1
				;;
		esac
	done

	if [ ""$homebrew_bundle_check" -o "$homebrew_outdated" -o "$homebrew_cask_outdated" -o $homebrew_bundle_cleanup" ]; then
		echo "--- brew update"
		local o="$(brew update)"
		if [ -n "$o" -a "$o" != "Already up-to-date." ]; then
			echo "$o" | indent
		fi
		eval_indent ''
	fi
	if [ "$homebrew_bundle_check" ]; then
		echo "--- brew bundle check"
		local o="$(brew bundle check --verbose --file="$BREW_BUNDLE_FILE_PATH")"
		if [ -n "$o" -a "$o" != "The Brewfile's dependencies are satisfied." ]; then
			echo "$o" | indent
		fi
	fi
	if [ "$homebrew_outdated" ]; then
		echo "--- brew outdated"
		eval_indent 'brew outdated --formula --verbose'
	fi
	if [ "$homebrew_cask_outdated" ]; then
		echo "--- brew cask outdated"
		eval_indent 'brew outdated --cask --verbose --greedy'
	fi
	if [ "$homebrew_bundle_cleanup" ]; then
		echo "--- brew bundle cleanup"
		eval_indent 'brew bundle cleanup --file="$BREW_BUNDLE_FILE_PATH"'
	fi
	if [ "$npm_outdated" ]; then
		echo "--- npm outdated"
		eval_indent 'npm outdated --global'
	fi
	if [ "$pyv_outdated" ]; then
		if [ -n "$PYV_ROOT_DIR" ]; then
			echo "--- pyv: $PYV_ROOT_DIR"
			eval_indent 'show_pyv_updates "$PYV_ROOT_DIR"'
		fi
	fi
	if [ "$macappstore_outdated" ]; then
		echo "--- mas outdated"
		eval_indent 'mas outdated'
	fi
	if [ "$macossystem_outdated" ]; then
		echo "--- softwareupdate --list"
		local o="$(softwareupdate --list 2>&1)"
		if [ -n "$o" -a "$o" != $'No new software available.\nSoftware Update Tool\n\nFinding available software' ]; then
			echo "$o" | indent
		fi
	fi
	echo ...
}


function show_pyv_updates() {
	rootdir="$1"
	local output=
	for venv in $(compgen -A directory "$rootdir/"); do
		local venv_name="$(basename "$venv")"
		if [ "${venv_name:0:1}" == "." ]; then
			continue
		fi
		output="$(eval_indent 'PYTHONWARNINGS="ignore:DEPRECATION" $venv/bin/pip --disable-pip-version-check list --outdated --not-required --format=json | jq -r '\''.[]|.name + "==" + .version + " < " + .latest_version'\')"
		if [ -z "$output" ]; then
			continue
		fi
		echo "--- ${venv#$rootdir/}"
		echo "$output"
	done
}


function eval_indent() {
	eval "$@" 2>&1 | indent
}


function indent() {
	sed 's/^/'$'\t''/'
}


if ! $(return >/dev/null 2>&1); then
	main "$@"
fi
