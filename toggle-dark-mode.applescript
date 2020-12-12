#!/usr/bin/env osascript -l AppleScript
#:AppBundleName: Toggle Dark Mode.app
#:CFBundleIdentifier: com.vruyr.toggle-dark-mode


tell application "System Events"
	tell appearance preferences
		set dark mode to not dark mode
	end tell
end tell
