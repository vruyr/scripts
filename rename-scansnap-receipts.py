#!/usr/bin/env python3

"""
Description
"""

import sys, locale, argparse, os, re


def main(
	*,
	# Example Options
	cd_path
):
	locale.setlocale(locale.LC_ALL, "")

	if cd_path:
		os.chdir(cd_path)

	p = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})_USD_(?P<sum>\d+\.\d+)_(?P<payee>.*).(?P<suffix>pdf)")
	for f in os.listdir():
		m = p.match(f)
		if not m:
			continue
		f_new = "{date} -${sum} {payee}.{suffix}".format(**m.groupdict())
		os.rename(f, f_new)


def parse_args(*, args, prog):
	parser = argparse.ArgumentParser(
		prog=prog,
		usage="%(prog)s [OPTIONS]...",
		description=__doc__,
		formatter_class=argparse.RawTextHelpFormatter,
		fromfile_prefix_chars="@",
		add_help=False,
	)

	the_default = "\ndefault: %(default)s"

	options_generic = parser.add_argument_group("Generic Options")
	options_generic.add_argument(
		"--help", "-h",
		action="help",
		help="show help message and exit",
	)

	options_example = parser.add_argument_group("Example Options")
	options_example.add_argument(
		"-C", metavar="PATH",
		action="store", dest="cd_path", type=str, default=None, required=False,
		help="Run as if git was started in PATH instead of the current working directory."
	)

	opts = parser.parse_args(args)
	return vars(opts)


def configure_logging(opts):
	pass


def smain(argv=None):
	if argv is None:
		argv = sys.argv

	try:
		opts = parse_args(args=argv[1:], prog=argv[0])
		configure_logging(opts)
		return main(**opts)
	except KeyboardInterrupt:
		print(file=sys.stderr)


if __name__ == "__main__":
	sys.exit(smain())
