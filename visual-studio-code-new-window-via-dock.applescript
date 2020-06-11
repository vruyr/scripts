#!/usr/bin/env osascript -l AppleScript

tell application "System Events"
	tell application process "Dock"
		set vscodeDockIcons to UI elements of list 1 whose title is "Visual Studio Code"
		if (count of vscodeDockIcons) is 0 then
			tell application "Visual Studio Code" to activate
		else
			set dockIcon to first item of vscodeDockIcons
			tell dockIcon to perform action "AXShowMenu"
			set newWindowMenuItem to menu item "New Window" of menu 1 of dockIcon
			tell newWindowMenuItem to perform action "AXPress"
		end if
	end tell
end tell
