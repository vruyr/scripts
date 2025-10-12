-- Compile with:
-- mkdir -p ~/Library/Scripts/"Folder Action Scripts"
-- osacompile -l AppleScript -o "$HOME/Library/Scripts/Folder Action Scripts/add - open or offer to view.scpt" "add - open or offer to view.applescript"
property dialog_timeout : 30 -- set the amount of time before dialogs auto-answer.

(*
add - new item alert

This Folder Action handler is triggered whenever items are added to the attached folder.
The script will display an alert containing the number of items added and offering the user
the option to reveal the added items in Finder.

Copyright © 2002–2007 Apple Inc.

You may incorporate this Apple sample code into your program(s) without
restriction.  This Apple sample code has been provided "AS IS" and the
responsibility for its operation is yours.  You are not permitted to
redistribute this Apple sample code as "Apple sample code" after having
made changes.  If you're going to redistribute the code, we require
that you make it clear that the code was descended from Apple sample
code, but that you've made changes.
*)

on adding folder items to this_folder after receiving added_items
	try
		tell application "Finder"
			--get the name of the folder
			set the folder_name to the name of this_folder
		end tell

		-- find out how many new items have been placed in the folder
		set the item_count to the number of items in the added_items
		--create the alert string
		set alert_message to ("Folder Actions Alert:" & return & return) as Unicode text
		if the item_count is greater than 1 then
			set alert_message to alert_message & (the item_count as text) & " new items have "
		else
			set alert_message to alert_message & "1 new item has "
		end if
		set alert_message to alert_message & "been placed in folder " & «data utxt201C» & the folder_name & «data utxt201D» & "."

		-- Append the added file names to the alert (minimal change)
		set _names to ""
		repeat with _it in added_items
			try
				tell application "Finder" to set _names to _names & "• " & (name of (_it as alias)) & return
			on error
				set _names to _names & "• " & (POSIX path of (_it as alias)) & return
			end try
		end repeat

		set the alert_message to (the alert_message & return & return & _names & return & return & "What would you like to do?")

		display dialog the alert_message buttons {"Open", "Reveal", "Nothing"} default button 3 with icon 1 giving up after dialog_timeout
		set the user_choice to the button returned of the result

		if user_choice is "Open" then
			repeat with f in added_items
				tell application "Finder" to open f
			end repeat
		else if user_choice is "Reveal" then
			tell application "Finder"
				--go to the desktop
				activate
				--open the folder
				open this_folder
				--select the items
				reveal the added_items
			end tell
		end if
	end try
end adding folder items to
