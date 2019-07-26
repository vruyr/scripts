#!/usr/bin/env osascript -l AppleScript

-- osacompile -l AppleScript -o "$HOME/Applications/Compiled AppleScript/Toggle Dark Mode.app" toggle-dark-mode.applescript

tell application "System Events"
	tell appearance preferences
		set dark mode to not dark mode
	end tell
end tell
