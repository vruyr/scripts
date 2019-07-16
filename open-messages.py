#!/usr/bin/env python3

"""
Usage:
	{prog} [--message=TEXT] [--just-print] (ADDRESS)...

Positional Parameters:
	ADDRESS  Message recipients

Options:
	--message, -m TEXT     The message text to pre-fill.
	--just-print, -n       Do not open Messages, just print the url that will.
"""

import sys, locale, os, urllib.parse
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
	just_print = params.pop("--just-print")
	assert not params, params

	params = {
		"addresses": ",".join(a for a in addresses)
	}

	if message_text:
		params["body"] = message_text

	url = urllib.parse.urlunsplit([
		"sms",
		"",
		"/open",
		urllib.parse.urlencode(params, quote_via=urllib.parse.quote),
		""
	])
	print(url)

	if not just_print:
		import webbrowser
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
