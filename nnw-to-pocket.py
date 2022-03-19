#!/usr/bin/env python3

import sys, re, time, subprocess
from unittest import result


def get_pasteboard():
	pb = subprocess.run(["pbpaste"], stdout=subprocess.PIPE, check=True, encoding="UTF-8").stdout.strip()
	return pb


def set_pasteboard(input, encoding=None):
	subprocess.run(["pbcopy"], input=input, encoding=encoding)


netnewswire_item_text_url_p = re.compile(r"^external URL: (.*)$", flags=re.M)

set_pasteboard(b"")

while True:
	urls = netnewswire_item_text_url_p.findall(get_pasteboard())
	if not urls:
		time.sleep(0.25)
		continue
	subprocess.run(["getpocket", "--dont-show-progress", "add", *urls])
	set_pasteboard(b"")
