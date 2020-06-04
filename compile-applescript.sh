#!/usr/bin/env bash

set -o errexit

if [ ! -e "$1" -o -z "$2" ]; then
	echo "USAGE: $0 <path-to.applescript> <Path To.app>" >&2
	exit 1
fi

applescript_path="$1"
app_path="$2"

osacompile -l AppleScript -o "$app_path" "$applescript_path"
defaults write "$app_path/Contents/Info.plist" LSUIElement -bool true
plutil -convert xml1 "$app_path/Contents/Info.plist"
osascript -e '
	tell application "System Preferences"
		activate
		reveal anchor "Privacy_Accessibility" of pane "com.apple.preference.security"
		authorize pane "com.apple.preference.security"
	end tell
'
