#!/usr/bin/env -S uv --quiet run --no-project --script --
# https://peps.python.org/pep-0723/
# https://github.com/astral-sh/uv
# /// script
# requires-python = ">=3.14,<4"
# dependencies = [
# ]
# ///

import sys, pathlib, os, datetime


def main(args):
	renames = []

	for filename in sys.argv[1:]:
		p = pathlib.Path(filename)
		t = datetime.datetime.fromtimestamp(p.lstat().st_ctime)
		t = t.astimezone()
		pp = p.parent / "{:%Y%m%dT%H%M%S%z} {}".format(t, p.name)
		if pp.exists():
			print("refusing to rename anything, destination already exist - ", pp)
			return
		renames.append((p, pp))

	for p, pp in renames:
		p.rename(pp)
		print(f"{p} -> {pp}")


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
