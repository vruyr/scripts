#!/Users/vruyr/.pyvenv/shell/bin/python
#!/usr/bin/env python

"""
Usage:
  normalize-dates.py (--iso|--file) [--utc|--local]

Output Format:
  --iso         Output the date in ISO 8601 format [default]
  --file        Output the date in a format suitable for a filename

Date/Time Conversion:
  --utc         Convert the date to UTC timezone
  --local       Convert the date to local timezone
"""

import sys, datetime
import dateutil.parser
import docopt


def main(argv=None):
	params = docopt.docopt(__doc__, version="UNVERSIONED")

	for line in sys.stdin.readlines():
		sline = line.strip()
		if not sline:
			output(line)
			continue

		try:
			d = dateutil.parser.parse(sline)
		except:
			output(line)
			continue

		if params["--local"]:
			d = d.astimezone(tz=None)
		elif params["--utc"]:
			d = d.astimezone(datetime.timezone.utc)

		if params["--iso"]:
			output(d.isoformat())
		elif params["--file"]:
			output("{:%Y%m%dT%H%M%S%z}".format(d))


def output(s, *, fo=sys.stdout):
	print(s, file=fo)
	fo.flush()


if __name__ == "__main__":
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		sys.stderr.write("\n")
