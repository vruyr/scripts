#!/usr/bin/env python3

"""
Usage:
	{prog} REGEX_PATTERN
"""

import sys, locale, os, re
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
	pattern = params.pop("REGEX_PATTERN")
	assert not params, params

	pattern = re.compile(pattern)

	the_input = os.fdopen(sys.stdin.fileno(), mode="rb", buffering=0)
	the_output = os.fdopen(sys.stdout.fileno(), mode="wb", buffering=0)

	did_save_position = False
	while line := the_input.readline():
		if pattern.match(line.decode()):
			if did_save_position:
				the_output.write(b"\x1b8\x1b[0J")
			else:
				the_output.write(b"\x1b7")
				did_save_position = True
		the_output.write(line)
		the_output.flush()


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
