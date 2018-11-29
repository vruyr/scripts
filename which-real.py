#!/usr/bin/env python3


"""
Usage:
	which-real.py <command>
"""


import sys, shutil, os, pathlib
# pip install 'docopt>=0.6.2,<0.7.0'
import docopt


def main(*, args):
	params = docopt.docopt(__doc__, argv=args, help=True, version=True, options_first=False)
	command = params.pop("<command>")
	assert not params, params

	print(command, end="\n\n")
	command_path = shutil.which(command)

	command_path_last = None
	while command_path_last != command_path:
		print(command_path)
		command_path_last = command_path

		parts = pathlib.Path(command_path).parts
		assert parts[0] == os.path.sep, parts[0]
		first = list(parts[:1])
		second = list(parts[1:])

		while second:
			first.append(second.pop(0))
			p = pathlib.Path(*first)
			if not p.is_symlink():
				continue
			t = os.readlink(p)
			print("\t", p, " -> ", t, sep="", end="\n\n")
			first = list(pathlib.Path(os.path.normpath((p.parent / t))).parts)
			command_path = os.fspath(pathlib.Path(*first) / pathlib.Path(*second))
			break
		else:
			continue
		command_path_last = None



def _ssmain():
	sys.exit(main(args=sys.argv[1:]))


if __name__ == '__main__':
	_ssmain()
