#!/usr/bin/env python3

import sys, re, time, subprocess


open_amazon_order_page = """
on run argv
	set orderId to item 1 of argv
	tell application "Safari"
		activate
		set URL of document 1 to ("https://www.amazon.com/gp/css/summary/print.html?orderID=" & orderId)
		set doc to document ("Amazon.com - Order " & orderId)
		tell doc to activate
	end tell
end run
"""

def get_pasteboard():
	return subprocess.run(["pbpaste"], stdout=subprocess.PIPE, check=True, encoding="UTF-8").stdout.strip()

def match_pasteboard(p):
	while (m := p.match(get_pasteboard())) is None:
		pass
	return m

order_id_p = re.compile(r"(?:Order)?\s*#?(\d{3}-\d{7}-\d{7})")
trn_p = re.compile(r"^(Visa) ending in (\d+):\s+(\w+ \d+, \d+):\s*\$(\d+\.\d+)$")

subprocess.run(["pbcopy"], input=b"")

while True:
	subprocess.Popen(["afplay", "/System/Library/Sounds/Morse.aiff"])
	m = match_pasteboard(order_id_p)
	amazon_order_id = m.group(1)

	print("https://www.amazon.com/gp/css/summary/print.html?orderID=" + amazon_order_id)
	subprocess.run(["osascript", "-e", open_amazon_order_page, amazon_order_id])

	subprocess.run(["pbcopy"], input=b"")
	subprocess.Popen(["afplay", "/System/Library/Sounds/Pop.aiff"])
	m = match_pasteboard(trn_p)
	card_type, card_num, trn_date, trn_sum = m.groups()
	trn_date = "{:04d}-{:02d}-{:02d}".format(*time.strptime(trn_date, "%B %d, %Y")[:3])
	result = f"{trn_date} -${trn_sum} [{card_type} {card_num}] Amazon.com - Order {amazon_order_id}"
	subprocess.run(["pbcopy"], encoding="UTF-8", input=result)
	print(result)
	subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
