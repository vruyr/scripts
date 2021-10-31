#!/usr/bin/env python3

from os import path
import pathlib, collections, json, subprocess


CONFIG_DIR = pathlib.Path.home() / ".config" / pathlib.Path(__file__).stem


def main():
	folders = collections.defaultdict(list)

	for label, url in read_config("accounts"):
		p = subprocess.run(
			["imap.py", "-a", url, "--json"],
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			shell=False
		)
		assert p.returncode == 0, p
		assert not p.stderr
		for entry in json.loads(p.stdout.decode()):
			path = entry["path"]
			path.insert(0, label)
			for p in path:
				assert "/" not in p
			folders[path[-1]].append("/".join(path))

	folders = {name: paths for name, paths in folders.items() if len(paths) != 1}
	print("\n\n".join(
		"\n".join(paths) for paths in folders.values()
	))


def read_config(name):
	with (CONFIG_DIR / (name + ".json")).open("r") as fo:
		return json.load(fo)


if __name__ == '__main__':
	main()
