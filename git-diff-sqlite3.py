#!/usr/bin/env python3

"""
Usage:
	{prog} PATH OLD_FILE OLD_HEX OLD_MODE NEW_FILE NEW_HEX NEW_MODE
"""


import sys, locale, os, subprocess
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
	path     = params.pop("PATH")
	old_file = params.pop("OLD_FILE")
	old_hex  = params.pop("OLD_HEX")
	old_mode = params.pop("OLD_MODE")
	new_file = params.pop("NEW_FILE")
	new_hex  = params.pop("NEW_HEX")
	new_mode = params.pop("NEW_MODE")
	assert not params, params

	header = (
		f"-- Path: {path}\n"
		f"-- Old: {old_mode} {old_hex}\n"
		f"-- New: {new_mode} {new_hex}\n"
	)

	# TODO:vruyr Make sure this will invoke the same git instance that invoked us.
	colorize = subprocess.run(["git", "config", "--get-colorbool", "color.diff"], shell=False, check=False).returncode == 0

	if not colorize:
		sys.stdout.write(header)
		sys.stdout.flush()

	p_d = subprocess.Popen(
		# https://www.sqlite.org/sqldiff.html
		["sqldiff", old_file, new_file],
		shell=False,
		stdout=subprocess.PIPE if colorize else None,
	)

	if colorize:
		# pip install 'Pygments>=2.4.2,<3.0.0'
		import pygments, pygments.lexers, pygments.formatters
		sys.stdout.write(pygments.highlight(
			(
				header
				+
				p_d.stdout.read().decode() # TODO:vruyr Make sure correct encoding will be used while decoding.
			),
			pygments.lexers.SqlLexer(),
			pygments.formatters.Terminal256Formatter(
				style="pastie",
				linenos=False,
				bg="light",
			),
		))

	p_d.wait()
	if p_d.returncode != 0:
		raise subprocess.SubprocessError(f"Error: sqldiff failed with return code {p_d.returncode}")


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
