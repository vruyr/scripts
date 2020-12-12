#!/usr/bin/env osascript -l AppleScript
#:AppBundleName: iTerm New Window.app
#:CFBundleIdentifier: com.vruyr.iterm-new-window

tell application "iTerm"
	create window with default profile
end tell
