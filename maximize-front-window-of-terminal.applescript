#!/usr/bin/env osascript -l AppleScript

on run argv
	set displayResolutionWidth to 1440
	set displayResolutionHeight to 900
	tell application "System Events"
		tell application process "Terminal"
			set theWindow to front window
			set position of theWindow to {0, 0}
			set size of theWindow to {displayResolutionWidth, displayResolutionHeight}
		end tell
	end tell
end run