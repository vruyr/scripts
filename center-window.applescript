#!/usr/bin/env osascript -l AppleScript


on run argv
	set {appName, windowName} to argv
	centerWindow(appName, windowName, 1024, 768)
end run


on centerWindow(applicationName, windowName, windowWidth, windowHeight)
	set displayResolutionWidth to 1440
	set displayResolutionHeight to 900
	set positionX to (displayResolutionWidth - windowWidth) / 2
	set positionY to (displayResolutionHeight - windowHeight) / 2
	tell application "System Events"
		tell application process applicationName
			tell window windowName
				set size to {windowWidth, windowHeight}
				set position to {positionX, positionY}
			end tell
		end tell
	end tell
end centerWindow

