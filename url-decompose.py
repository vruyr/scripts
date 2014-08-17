#!/usr/bin/env python3

import sys, urllib.parse
import pprint


def main(args):
	urls = args[1:]

	if not urls:
		print("Paste URLs here one per line. Press Ctrl-D when done to exit.\n")
		urls = sys.stdin

	for url in urls:
		print("---")
		pprint.pprint(digest_url(url.rstrip()))
		print("---")


def digest_url(url):
	scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url)
	return {
		"0. scheme": scheme,
		"1. netloc": netloc,
		"2. path": path,
		"3. params": params,
		"4. query": urllib.parse.parse_qs(query, keep_blank_values=True),
		"5. fragment": fragment,
	}


if __name__ == '__main__':
	sys.exit(main(sys.argv))
