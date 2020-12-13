#!/usr/bin/env bash

set -o errexit

if [ ! -e "$1" ]; then
	echo >&2 "USAGE: $0 <path/to/script.applescript>"
	exit 1
fi

applescript_path="$1"

function trim() {
	local var="${1:-$(cat)}"
	var="${var#"${var%%[![:space:]]*}"}"
	var="${var%"${var##*[![:space:]]}"}"
	printf '%s' "$var"
}

app_path="$(sed -n 's/^#:AppBundleName:\(.*\)$/\1/p' <"$applescript_path" | trim)"
app_bundle_id="$(sed -n 's/^#:CFBundleIdentifier:\(.*\)$/\1/p' <"$applescript_path" | trim)"
is_lsuielement="$(sed -n 's/^#:LSUIElement:\(.*\)$/\1/p' <"$applescript_path" | trim)"
is_lsuielement=${is_lsuielement:-true}

test -n "$app_path" || {
	echo >&2 "Error: AppBundleName is not defined in the script."
	false
}

test -n "$app_bundle_id" || {
	echo >&2 "Error: CFBundleIdentifier is not defined in the script."
	false
}

app_dir="$HOME/Applications/Compiled Applescript"
mkdir -p "$app_dir"
app_path="$app_dir/${app_path%.app}.app"

osacompile -l AppleScript -o "$app_path" "$applescript_path"
defaults write "$app_path/Contents/Info.plist" LSUIElement -bool "$is_lsuielement"
defaults write "$app_path/Contents/Info.plist" CFBundleIdentifier -string "$app_bundle_id"
plutil -convert xml1 "$app_path/Contents/Info.plist"

while [ "$app_bundle_id" != "$(mdls -raw -name kMDItemCFBundleIdentifier "$app_path")" ]; do
	sleep 0.25s
	printf '.'
done
printf '\n'

tccutil reset All "$app_bundle_id" || {
	echo >&2 "Error Privacy settings were not reset - please remove and re-add the app manually."
}

osascript -e '
	tell application "System Preferences"
		activate
		reveal anchor "Privacy_Accessibility" of pane "com.apple.preference.security"
		authorize pane "com.apple.preference.security"
	end tell
	""
'

mdfind 'kMDItemCFBundleIdentifier = "'"$app_bundle_id"'"'
