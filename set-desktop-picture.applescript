#!/usr/bin/env osascript

on run (args)
	# https://apple.stackexchange.com/a/69199
	set p to POSIX file "/Library/Desktop Pictures/Solid Colors/Solid Gray Pro Ultra Dark.png"
	log "Setting the desktop picture to \"" & POSIX path of p & "\""
	tell application "System Events"
		set picture of every desktop to p
	end tell
end run
