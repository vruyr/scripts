#!/usr/bin/env osascript -l AppleScript

tell application "System Events" to set theApp to first application process whose bundle identifier is "com.microsoft.VSCode"
tell application (path of file of theApp) to activate
tell application "System Events" to tell theApp to tell menu item "New Window" of menu "File" of menu bar item "File" of menu bar 1 to click
