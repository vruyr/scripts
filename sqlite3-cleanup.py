#!/usr/bin/env python3

"""
Executes a no-op sqlite3 statement to cleanup any residual temporary files, such as -wal or -shm.

Usage:
	{prog} SQLITE_FILE_PATH
"""

import sys, os, sqlite3
# pip install 'docopt>=0.6.2'
import docopt


def main(*, args, prog):
	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	database_path = params.pop("SQLITE_FILE_PATH")
	assert database_path
	assert not params, params

	with sqlite3.connect(database_path) as connection:
		connection.execute("select * from sqlite_master;")


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
