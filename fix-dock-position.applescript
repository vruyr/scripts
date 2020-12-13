#!/usr/bin/env osascript -l AppleScript
#:AppBundleName: Fix Dock Position.app
#:CFBundleIdentifier: com.vruyr.fix-dock-position

tell application "System Events"
	set autohide of dock preferences to not autohide of dock preferences
	delay 0.25
	set autohide of dock preferences to not autohide of dock preferences
	do shell script "python -c '
import Quartz.CoreGraphics as cg
cg.CGEventPost(
	cg.kCGHIDEventTap,
	cg.CGEventCreateMouseEvent(
		None,
		cg.kCGEventMouseMoved,
		cg.CGDisplayBounds(cg.CGMainDisplayID()).size,
		cg.kCGMouseButtonLeft
	)
)
'"
end tell
