#!/usr/bin/env python3

import pathlib, itertools, collections, json, sys, subprocess


def main():
	folders = collections.defaultdict(list)

	for server, username in [
		["10.0.7.10", "vruyr@mechena.com"],
		["imap.gmail.com", "vruyr@vruyr.com"]
	]:
		p = subprocess.run(
			["imap.py", "-l", "--json", "-s", server, "-u", username],
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			shell=False
		)
		assert p.returncode == 0, p
		assert not p.stderr
		for entry in json.loads(p.stdout.decode()):
			path = entry["path"]
			path.insert(0, username)
			for p in path:
				assert "/" not in p
			folders[path[-1]].append("/".join(path))

	folders = {name: paths for name, paths in folders.items() if len(paths) != 1}
	for paths in folders.values():
		if len(paths) == 1:
			continue
		print("\n".join(paths), end="\n\n")
	# json.dump(folders, sys.stdout, indent=4)


if __name__ == '__main__':
	main()
