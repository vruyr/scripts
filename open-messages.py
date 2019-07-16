#!/usr/bin/env python3

"""
Usage:
	{prog} [--message=TEXT] (ADDRESS)...

Positional Parameters:
	ADDRESS  Message recipients

Options:
	--message, -m TEXT     The message text to pre-fill.
"""

import sys, locale, os, urllib.parse, webbrowser
# pip install docopt==0.6.2
import docopt


def main(*, args, prog):
	locale.setlocale(locale.LC_ALL, "")

	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	addresses = params.pop("ADDRESS")
	message_text = params.pop("--message")
	assert not params, params

	params = {
		"addresses": ",".join(a for a in addresses)
	}

	if message_text:
		params["body"] = message_text

	url = urllib.parse.urlunsplit(["sms", "", "/open", urllib.parse.urlencode(params), ""])
	print(url)
	webbrowser.open(url)


def smain(argv=None):
	if argv is None:
		argv = sys.argv

	try:
		return main(
			args=argv[1:],
			prog=argv[0]
		)
	except KeyboardInterrupt:
		print(file=sys.stderr)


if __name__ == "__main__":
	sys.exit(smain())
