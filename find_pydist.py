#!/usr/bin/env python3

"""
Usage:
	{prog} (--file=PATH|--module=NAME)

Options:
	--file, -f PATH    Identify the distribution if the specified file.
	--module, -m NAME  Identify the distribution if the specified python module.
"""

import sys, os, csv, importlib
# pip install 'docopt>=0.6.2'
import docopt
# pip install 'setuptools>=40.6.3'
import pkg_resources


def main(*, args, prog):
	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	file_path = params.pop("--file")
	module_name = params.pop("--module")
	assert bool(file_path) != bool(module_name), (file_path, module_name)
	assert not params, params

	if module_name:
		file_path = importlib.import_module(module_name).__file__

	dist = find_dist_by_filepath(file_path)

	if dist is not None:
		print(dist.as_requirement())
	else:
		print("not found")



def find_dist_by_filepath(the_path):
	for dist in pkg_resources.working_set:
		if not dist.has_metadata("RECORD"):
			continue

		record = dist.get_metadata_lines("RECORD")
		entries = csv.reader(record, delimiter=",", quotechar="\"", lineterminator=os.linesep)
		for file_path, file_hash, file_size in entries:
			file_path_full = os.path.join(dist.location, file_path)
			if file_path_full == the_path:
				return dist


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
