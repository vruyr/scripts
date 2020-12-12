#!/usr/bin/env osascript -l AppleScript
#:AppBundleName: Set Up Bluetooth Keyboard.app
#:CFBundleIdentifier: com.vruyr.set-up-bluetooth-keyboard

tell application "System Preferences"
	activate
	reveal anchor "keyboardTab" of pane "com.apple.preference.keyboard"
end tell
delay 1
tell application "System Events" to tell process "System Preferences"
	click button "Set Up Bluetooth Keyboard…" of window 1
end tell
