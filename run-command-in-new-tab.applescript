#!/usr/bin/env osascript -l AppleScript


on run argv
	set {command} to argv
	tell application "Terminal" to activate
	tell application "System Events" to keystroke "t" using {command down}
	tell application "Terminal" to do script command in front window
	return -- anything returned will be sent to stdout
end run
