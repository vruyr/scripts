#!/usr/bin/env osascript -l AppleScript

tell application "System Events"
	tell application process "Dock"
		set dockIcon to first item of (UI elements of list 1 whose title is "Visual Studio Code")
		tell dockIcon to perform action "AXShowMenu"
		set newWindowMenuItem to menu item "New Window" of menu 1 of dockIcon
		tell newWindowMenuItem to perform action "AXPress"
	end tell
end tell
