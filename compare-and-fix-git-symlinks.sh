#!/usr/bin/env bash

test "${BASH_VERSINFO[0]}" == "4" || {
	echo "unsupported bash version"
	exit 1
}

set -o errexit
trap onexit EXIT
trap onerror ERR

function main() {
	local old_IFS="$IFS"
	local IFS=$'\n'
	affected_files=(
		$(git status --porcelain=v1 | sed -n 's/^ T \(.*\)$/\1/p')
	)
	IFS="$old_IFS"
	for affected_file in "${affected_files[@]}"; do
		if [ ! -e "$affected_file" ]; then
			echo "Need the file as sole parameter." >&2
			return 1;
		fi

		symlink_target=$(git cat-file -p "@:$affected_file")
		if diff -q "$symlink_target" "$affected_file" >/dev/null; then
			ln -vsf "$symlink_target" "$affected_file"
		else
			bcomp "$symlink_target" "$affected_file" || true
		fi
		# echo "'$affected_file' -> '$symlink_target'"
		# read -p "Replace? [Y/n] " REPLY
		# if [ "${REPLY,,}" == "y" -o "${REPLY,,}" == "yes" -o -z "$REPLY" ]; then
		# 	ln -vsf "$symlink_target" "$affected_file"
		# fi
	done
}

function onexit() {
	:
}

function onerror() {
	declare -p BASH_COMMAND
	echo "ERROR"
}

main "$@"
