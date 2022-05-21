#!/usr/bin/env osascript -l AppleScript

set previousCipboard to (the clipboard)
repeat
	repeat 1 times
		if (the clipboard) is equal to previousCipboard then
			exit repeat
		end if
		set previousCipboard to (the clipboard)
		log (previousCipboard)
		set currentApp to (path to frontmost application as text)
		activate application "Pocket"
		tell application "System Events" to keystroke "s" using command down
		activate application currentApp
	end repeat
end repeat
