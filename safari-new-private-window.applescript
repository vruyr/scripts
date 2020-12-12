#!/usr/bin/env osascript -l AppleScript
#:AppBundleName: Safari New Private Window.app
#:CFBundleIdentifier: com.vruyr.safari-new-private-window

tell application "System Events"
	tell application process "Safari"
		tell menu item "New Private Window" of menu "File" of menu bar item "File" of menu bar 1 to click
	end tell
end tell
tell application "Safari" to activate
