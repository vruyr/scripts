#!/usr/bin/env python3

from __future__ import print_function
import sys; assert sys.version_info[:2] in [(3, 5), (3, 6)]
import email, email.utils, pathlib, os


def main(args):
	if len(args) != 1:
		raise TypeError("need 1 and only 1 argument")
	emlpath = pathlib.Path(args[0])

	with open(emlpath, "rb") as fo:
		msg = email.message_from_bytes(fo.read())

	date_str = "{:%Y%m%dT%H%M%S%z}".format(email.utils.parsedate_to_datetime(msg["date"]))
	from_name, from_address = email.utils.parseaddr(msg["from"])
	subject_str = msg["subject"]

	journal_entry_name = "{date} [{sender_name} {sender_address}] {subject}".format(
		date=date_str,
		sender_name=from_name,
		sender_address=from_address,
		subject=subject_str,
	)

	journal_entry_path = emlpath.parent / journal_entry_name
	journal_entry_path.mkdir()
	destemlpath = journal_entry_path / emlpath.name
	emlpath.rename(destemlpath)

	print(destemlpath)


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
