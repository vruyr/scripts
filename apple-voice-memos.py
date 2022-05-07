#!/usr/bin/env python3

"""
Description
"""

from ast import DictComp
from multiprocessing import context
import sys, locale, argparse, pathlib, urllib.parse, contextlib, sqlite3, datetime
# pip install pytz==2022.1
import pytz


def main(
	*,
	# Example Options
	example
):
	locale.setlocale(locale.LC_ALL, "")

	cloud_recordings_db = pathlib.Path.home() / "Library" / "Application Support" / "com.apple.voicememos" / "Recordings" / "CloudRecordings.db";
	db_uri = urllib.parse.urljoin(cloud_recordings_db.as_uri(), "?mode=ro")

	query = """
		select ZFOLDER.ZENCRYPTEDNAME, ZDATE, ZDURATION, ZCUSTOMLABEL, ZPATH
		from ZCLOUDRECORDING
		left join ZFOLDER
		on ZCLOUDRECORDING.ZFOLDER = ZFOLDER.Z_PK
	"""

	with contextlib.ExitStack() as stack:
		conn = stack.enter_context(contextlib.closing(sqlite3.connect(db_uri, uri=True)))
		cursor = conn.cursor()
		stack.enter_context(contextlib.closing(cursor))
		cursor.execute(query)
		for folder, date, duration, label, path in cursor.fetchall():
			date = datetime_from_coredata_float(date).astimezone()
			print(
				"\n{:%F %T %z} [{}] {}\n[{}] {}\n".format(
					date,
					format_duration(duration, compact=True),
					label,
					folder,
					path,
				),
				sep="",
				end="\n"
			)


def datetime_from_coredata_float(f):
	result = datetime.datetime(2001, 1, 1)
	result += datetime.timedelta(seconds=f)
	result = result.replace(tzinfo=datetime.timezone.utc)
	return result


def format_duration(seconds, *, compact=False):
	seconds = round(seconds)
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)
	if compact:
		return f"{hours}h{minutes}m{seconds}s".removeprefix("0h").removeprefix("0m")
	else:
		return f"{hours}h {minutes:2}m {seconds:2}s"


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
		"--example", "-e", metavar="NUMBER",
		action="store", dest="example", type=int, default=None,
		help="an example option that accepts an integer" + the_default
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
