#!/usr/bin/env osascript -l AppleScript

on run argv
	tell application "System Events"
		--set dock size of dock preferences to 0.285714298487
		set dock size of dock preferences to 0.181
		
		set prefs to dock size of dock preferences
		set defaults to do shell script "defaults read com.apple.dock tilesize"
		tell application process "Dock" to set uielt to size of list 1
		return {defaults, prefs, uielt}
	end tell
end run
