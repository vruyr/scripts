#!/usr/bin/env osascript -l AppleScript

-- osacompile -l AppleScript -o "$HOME/Applications/Compiled AppleScript/Toggle Dark Mode.app" toggle-dark-mode.applescript
-- defaults write "$HOME/Applications/Compiled AppleScript/Toggle Dark Mode.app/Contents/Info.plist" LSUIElement -bool true
-- plutil -convert xml1 "$HOME/Applications/Compiled AppleScript/Toggle Dark Mode.app/Contents/Info.plist"
-- open x-apple.systempreferences:com.apple.preference.security?Privacy

tell application "System Events"
	tell appearance preferences
		set dark mode to not dark mode
	end tell
end tell
