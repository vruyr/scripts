#!/usr/bin/env python3

"""
Usage:
	{prog} [options] [--ignore=REGEX...] [-v...] [-q...] <folder>

Options:
	--ignore, -i REGEX  Ignore files and folders that match the pattern.
	--null, -0          Use a null char instead of a newline as a separator.
	--recursive, -r     Monitor for new files and folders recursively.
	--verbose, -v       Increase output verbosity.
	--quiet, -q         Decrease output verbosity.
	--silent, -s        No not produce any output.
"""

import sys, locale, os, re, pathlib
# pip install docopt==0.6.2
import docopt
# pip install watchdog==2.0.2
import watchdog.observers, watchdog.events


def main(*, args, prog):
	locale.setlocale(locale.LC_ALL, "")

	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	folder_to_observe = pathlib.Path(params.pop("<folder>")).resolve()
	ignore_patterns = params.pop("--ignore")
	separator = "\0" if params.pop("--null") else "\n"
	observe_recursively = params.pop("--recursive")
	output_verbosity = params.pop("--verbose")
	output_verbosity -= params.pop("--quiet")
	if params.pop("--silent"):
		output_verbosity = float("-inf")
	assert not params, params

	if output_verbosity >= 0:
		print("Monitoring", repr(folder_to_observe), file=sys.stderr)

	observer = watchdog.observers.Observer()
	handler = FilesystemEventHandler(
		path=folder_to_observe,
		output=sys.stdout,
		ignore=ignore_patterns,
		sep=separator,
		output_verbosity=output_verbosity,
	)
	observer.schedule(handler, path=folder_to_observe, recursive=observe_recursively)
	observer.start()
	observer.join()


class FilesystemEventHandler(watchdog.events.FileSystemEventHandler):
	def __init__(self, *, path, output, ignore, sep, output_verbosity):
		self._observed_folder = pathlib.Path(path).resolve()
		self._output = output
		self._ignore = list(map(lambda p: re.compile(p), ignore))
		self._sep = sep
		self._output_verbosity = output_verbosity

	def on_new_path(self, path):
		path = pathlib.Path(path).relative_to(self._observed_folder).as_posix()
		if self._ignore and any(re.search(p, path) is not None for p in self._ignore):
			return
		if self._output_verbosity >= 1:
			print("New path:", path, file=sys.stderr)
		assert self._sep not in path, path
		self._output.write(path)
		self._output.write(self._sep)
		self._output.flush()


	def on_moved(self, event):
		if self._output_verbosity >= 1:
			print(event, file=sys.stderr)
		if pathlib.Path(event.dest_path).parent.parts == self._observed_folder.parts:
			self.on_new_path(event.dest_path)

	def on_created(self, event):
		if self._output_verbosity >= 1:
			print(event, file=sys.stderr)
		pass
		self.on_new_path(event.src_path)

	def on_deleted(self, event):
		if self._output_verbosity >= 2:
			print(event, file=sys.stderr)
		pass

	def on_modified(self, event):
		if self._output_verbosity >= 2:
			print(event, file=sys.stderr)
		pass

	def on_closed(self, event):
		if self._output_verbosity >= 2:
			print(event, file=sys.stderr)
		pass


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
