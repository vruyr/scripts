#!/usr/bin/env bash

set -o errexit

function find_vscode() {
	local IFS=$'\n'
	local apps=(
		$(mdfind 'kMDItemKind == "Application" && kMDItemCFBundleIdentifier == "com.microsoft.VSCode"') 
	)

	if [ "${#apps[@]}" != 1 ]; then
		echo >&2 "Expected to find exactly one app but found none or multiple:"
		echo >&2 "${apps[*]}"
		echo >&2 "---"
		return 1
	fi

	echo "${apps[@]}"
	return 0
}

VSCODE=$(find_vscode)
CONTENTS="$VSCODE/Contents"
ELECTRON="$CONTENTS/MacOS/Electron"
CLI="$CONTENTS/Resources/app/out/cli.js"
ATOM_SHELL_INTERNAL_RUN_AS_NODE=1 "$ELECTRON" "$CLI" "$@"
exit $?