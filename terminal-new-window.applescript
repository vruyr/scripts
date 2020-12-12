#!/usr/bin/env osascript -l AppleScript
#:AppBundleName: Terminal New Window.app
#:CFBundleIdentifier: com.vruyr.terminal-new-window

tell application "System Events"
	set pp to application processes whose bundle identifier is "com.apple.Terminal"
	if (count of pp) is not 0 then
		set theApp to first item of pp
		tell first menu item of menu "New Window" of menu item "New Window" of menu "Shell" of menu bar item "Shell" of menu bar 1 of theApp to click
	end if
end tell
tell application "Terminal" to activate
