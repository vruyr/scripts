#!/usr/bin/env osascript -l AppleScript


tell application "System Events"
	tell appearance preferences
		set dark mode to not dark mode
	end tell
end tell
