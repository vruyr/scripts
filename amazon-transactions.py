#!/usr/bin/env python3

import sys, re, time, subprocess
# pip install pyobjc
from AppKit import NSPasteboard, NSPasteboardTypeString, NSStringPboardType


open_amazon_order_page = """
-- https://alexwlchan.net/2020/06/using-applescript-to-open-a-url-in-private-browsing-in-safari/
on openUrlInNonPrivateWindow(urlToOpen)
	tell application "Safari"
		activate

		tell application "System Events"
			click menu item "New Window" of ¬
				menu "File" of menu bar 1 of ¬
				application process "Safari"
		end tell

		-- The frontmost window is the Non-Private Browsing window that just got opened -- change the URL to the one we want to open.
		tell window 1 to set properties of current tab to {URL:urlToOpen}
	end tell
end openUrlInNonPrivateWindow

on openUrlInNewTab(theUrl)
	tell application "Safari"
		activate
		if (count of windows) < 1 then
			my openUrlInNonPrivateWindow(theUrl)
		else
			tell window 1
				set current tab to (make new tab with properties {URL:theUrl})
			end tell
		end if
	end tell
end openUrlInNewTab

-- https://alexwlchan.net/2021/04/detect-private-browsing/
on isFrontmostSafariWindowPrivateBrowsing()
	-- If you don't activate Safari, the results are sometimes wrong.
	-- In particular, System Events doesn't have the most up-to-date
	-- information about the state of the menu.
	--
	-- I think this is the same problem as described in
	-- https://www.reddit.com/r/applescript/comments/an1cpj/information_in_system_events_not_updating/
	tell application "Safari" to activate

	tell application "System Events"
		set theWindowMenu to menu "Window" of ¬
			menu bar 1 of ¬
			application process "Safari"

		return (menu item "Move Tab to New Private Window" of theWindowMenu) exists
	end tell
end isFrontmostSafariWindowPrivateBrowsing

on getFrontmostSafariDocumentUrl()
	tell application "Safari"
		activate
		if (count of documents) < 1 then
			return ""
		end if
		return URL of document 1
	end tell
end getFrontmostSafariDocumentUrl

on setFrontmostSafariDocumentUrl(theUrl)
	tell application "Safari"
		activate
		set URL of document 1 to theUrl
	end tell
end setFrontmostSafariDocumentUrl

on run argv
	set orderId to item 1 of argv
	set theUrlBase to "https://www.amazon.com/gp/css/summary/print.html?orderID="
	set theUrl to (theUrlBase & orderId)

	if isFrontmostSafariWindowPrivateBrowsing() then
		openUrlInNonPrivateWindow(theUrl)
	else
		if getFrontmostSafariDocumentUrl() starts with theUrlBase then
			setFrontmostSafariDocumentUrl(theUrl)
		else
			openUrlInNewTab(theUrl)
		end if
	end if
end run
"""


pasteboard = NSPasteboard.generalPasteboard()
previous = None
amazon_order_id = None


def get_pasteboard_content() -> str:
	content = pasteboard.stringForType_(NSPasteboardTypeString)
	return content

def set_pasteboard_content(s):
	global previous
	pasteboard.clearContents()
	pasteboard.setString_forType_(s, NSStringPboardType)
	previous = s


order_id_p = re.compile(r"(?i:Order(?: ID)?|Your Amazon\.com order)?\s*#?\s*?(\d{3}-\d{7}-\d{7})\b")
transaction_p = re.compile(r"^(Visa) ending in (\d+):\s+(\w+ \d+, \d+):\s*\$([\d,]+\.\d+)$")


def process_input_string(s):
	global amazon_order_id
	if m := order_id_p.match(s):
		amazon_order_id = m.group(1)
		print("https://www.amazon.com/gp/css/summary/print.html?orderID=" + amazon_order_id)
		set_pasteboard_content(amazon_order_id)
		subprocess.run(["osascript", "-e", open_amazon_order_page, amazon_order_id])
		subprocess.Popen(["afplay", "/System/Library/Sounds/Pop.aiff"])
	elif m := transaction_p.match(s):
		card_type, card_num, trn_date, trn_sum = m.groups()
		trn_date = "{:04d}-{:02d}-{:02d}".format(*time.strptime(trn_date, "%B %d, %Y")[:3])
		result = f"{trn_date} -${trn_sum} [{card_type} {card_num}] Amazon.com - Order {amazon_order_id}.pdf"
		set_pasteboard_content(result)
		print(result)
		subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])


subprocess.Popen(["afplay", "/System/Library/Sounds/Morse.aiff"])
previous = get_pasteboard_content()
process_input_string(previous)

while True:
	current = get_pasteboard_content()
	if previous == current:
		time.sleep(0.25)
		continue
	previous = current

	process_input_string(current)
