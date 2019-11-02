#!/usr/bin/env osascript -l AppleScript

on run argv
	if (count of argv) is not 1 then
		error "USAGE: activate-vmware-vm-window.applescript <vm_name>"
	end if

	set theVmName to item 1 of argv

	tell application "System Events"
		tell application process "VMware Fusion"
			set theWindowMenu to menu "Window" of menu bar 1
			set theMenuItem to missing value
			repeat with aMenuItemIndex from (count of menu items of theWindowMenu) to 1 by -1
				set aMenuItem to menu item aMenuItemIndex of theWindowMenu
				set aMenuItemName to (name of aMenuItem as string)
				if aMenuItemName is theVmName then
					set theMenuItem to aMenuItem
					exit repeat
				end if
			end repeat
			if theMenuItem is missing value then
				error "Failed to find the " & quoted form of theVmName & " VM."
			end if
			tell application "VMware Fusion" to activate
			tell theMenuItem to click
		end tell
	end tell
	return ""
end run
