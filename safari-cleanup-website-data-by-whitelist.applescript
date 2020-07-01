#!/usr/bin/env osascript -l AppleScript

on run
	set whitelistFilePath to (POSIX path of (path to home folder)) & "/.config/safari-data-whitelist.txt"
	set websiteOriginWhitelist to splitString(read POSIX file whitelistFilePath, "
")
	set ansiGreen to ansiEscape("[32m")
	set ansiRed to ansiEscape("[31m")
	set ansiReset to ansiEscape("[0m")
	
	activate application "/Applications/Safari.app"
	delay 1
	tell application "System Events"
		set p to every process whose (bundle identifier is "com.apple.Safari" or POSIX path of application file is "/Applications/Safari.app")
		if (count of p) is 0 then
			error "Safari does not seem to be running."
		else if (count of p) > 1 then
			error "More than one processes of Safari found - can't choose one."
		end if
		set p to first item of p
		tell p
			keystroke "," using command down
			set prefsWindow to window 1
			click button "Privacy" of toolbar 1 of prefsWindow
			click button "Manage Website DataÉ" of group 1 of group 1 of prefsWindow
			set websiteDataSheet to sheet 1 of prefsWindow
			
			set mustStop to false
			repeat until mustStop
				set mustStop to true
				
				set websitesTable to table 1 of scroll area 1 of websiteDataSheet
				repeat while (count of (every row of websitesTable)) is 0
					delay 0.25
				end repeat
				
				-- See https://stackoverflow.com/a/36906011
				set focused of websitesTable to true
				tell websitesTable to keystroke "a" using command down -- select all rows
				
				set previousRowCount to count of every row of websitesTable
				set numToRemove to 0
				
				repeat with r in every row of websitesTable
					if (count of UI elements of r) is not 1 then
						error "Unexpected UI element structure."
					end if
					set websiteOrigin to my getOriginFromWebsiteDataDescription(name of UI element 1 of r)
					set mustRemove to true
					repeat with o in websiteOriginWhitelist
						if websiteOrigin is o as string then
							set mustRemove to false
							exit repeat
						end if
					end repeat
					if mustRemove then
						log ansiRed & "Removing: " & websiteOrigin & ansiReset
						set numToRemove to numToRemove + 1
					else
						log ansiGreen & "Keeping:  " & websiteOrigin & ansiReset
						set selected of r to false
					end if
				end repeat
				
				if numToRemove > 0 then
					set expectedRowCount to previousRowCount - numToRemove
					click button "Remove" of websiteDataSheet
					repeat while expectedRowCount is (count of every row of websitesTable)
						delay 0.25
					end repeat
					
					delay 1 -- TODO This is a hack. Figure out a way to prevent the race condition, for example by monitoring changes in the data sheet and proceeding only after a timeout of inactivity.
					
					log "Remaining:"
					set websitesTable to table 1 of scroll area 1 of websiteDataSheet
					repeat with r in every row of websitesTable
						log "	" & my getOriginFromWebsiteDataDescription(name of UI element 1 of r)
					end repeat
				else
					log "Nothing to remove."
				end if
				
				click button "Done" of websiteDataSheet
				tell (every button of prefsWindow whose subrole is "AXCloseButton") to click
				
				if mustStop then
					exit repeat
				end if
			end repeat
		end tell
	end tell
	return
end run

on ansiEscape(code)
	return (ASCII character 27) & code
end ansiEscape

on getOriginFromWebsiteDataDescription(descriptionString)
	set websiteDataTypeNames to {" Cache", " Cookies", " Databases", " Local Storage", " HSTS Policy", ","}
	
	set theResult to descriptionString
	set mustStop to false
	repeat until mustStop
		set mustStop to true
		repeat with n in websiteDataTypeNames
			if theResult ends with n then
				set mustStop to false
				set theResult to characters 1 thru (-1 + -(count of n)) of theResult as string
			end if
		end repeat
	end repeat
	return theResult
end getOriginFromWebsiteDataDescription


on splitString(theString, theDelimiter)
	set oldDelimiters to AppleScript's text item delimiters
	set AppleScript's text item delimiters to theDelimiter
	set theArray to {}
	repeat with l in every text item of theString
		set ll to l as string
		if ll is not "" and item 1 of ll is not "#" then
			copy ll to the end of theArray
		end if
	end repeat
	set AppleScript's text item delimiters to oldDelimiters
	return theArray
end splitString
