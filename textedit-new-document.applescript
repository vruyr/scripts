#!/usr/bin/env osascript -l AppleScript
#:AppBundleName: TextEdit New Document.app
#:CFBundleIdentifier: com.vruyr.textedit-new-document

tell application "TextEdit"
	activate
	make new document
end tell
