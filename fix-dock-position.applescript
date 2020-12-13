#!/usr/bin/env osascript -l AppleScript
#:AppBundleName: Fix Dock Position.app
#:CFBundleIdentifier: com.vruyr.fix-dock-position
#:LSUIElement: false

tell application "System Events"
	set autohide of dock preferences to not autohide of dock preferences
	delay 0.25
	set autohide of dock preferences to not autohide of dock preferences
	do shell script "python -c '
import Quartz.CoreGraphics as cg
x, y = cg.CGDisplayBounds(cg.CGMainDisplayID()).size
x -= 20
y -= 20
cg.CGEventPost(
	cg.kCGHIDEventTap,
	cg.CGEventCreateMouseEvent(
		None,
		cg.kCGEventMouseMoved,
		(x, y),
		cg.kCGMouseButtonLeft
	)
)
'"
end tell
