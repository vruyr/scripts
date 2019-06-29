#!/usr/bin/env osascript -l AppleScript

tell application "System Events"
	set theApp to first application process whose bundle identifier is "com.apple.Terminal"
	tell first menu item of menu "New Window" of menu item "New Window" of menu "Shell" of menu bar item "Shell" of menu bar 1 of theApp to click
end tell
tell application "Terminal" to activate
