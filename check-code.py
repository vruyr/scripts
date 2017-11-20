#!/usr/bin/env python3

import sys, argparse, re, subprocess, functools, fnmatch, pathlib, json

def main(argv=None):
	settings = {
		"args": []
	}
	settings_file_path = pathlib.Path("~/.check-code.json").expanduser()
	if settings_file_path.exists():
		settings = json.loads(settings_file_path.read_text("UTF-8"))
	opts = _parse_args(argv=[argv[0], *settings["args"], *argv[1:]])
	if opts.verbose:
		print(opts.skip)

	files = []

	object_hash = None
	object_hash_type = None

	if opts.since is not None:
		object_hash = opts.since
		p = subprocess.run(["git", "cat-file", "-t", object_hash], stdout=subprocess.PIPE)
		p.check_returncode()
		object_hash_type = p.stdout.decode().strip()
	else:
		p = subprocess.run(["git", "hash-object", "-w", "-t", "tree", "/dev/null"], stdout=subprocess.PIPE)
		p.check_returncode()
		object_hash = p.stdout.decode().strip()
		object_hash_type = None

	if object_hash_type == None:
		object_hash_mnemonic = f"$(git hash-object -w -t tree /dev/null)"
	elif object_hash_type == "tree":
		object_hash_mnemonic = object_hash
	elif object_hash_type == "commit":
		object_hash_mnemonic = f"$(git merge-base {opts.since} HEAD)"
		p = subprocess.run(["git", "merge-base", opts.since, "HEAD"], stdout=subprocess.PIPE)
		p.check_returncode()
		object_hash = p.stdout.decode().strip()

	if opts.verbose:
		print(f"git diff {object_hash_mnemonic}")
		print("---")
	p = subprocess.run(["git", "diff", "--name-status", object_hash], stdout=subprocess.PIPE)
	p.check_returncode()
	for file in p.stdout.decode().splitlines():
		status, file = re.split(r"\s+", file, maxsplit=1)
		assert status in ["A", "M"]
		files.append(file)

	results = []

	for file in files:
		with open(file, "r") as fo:
			tags = set()
			for lineno, line in enumerate(fo.readlines()):
				check_indentions(tags, line, file, lineno)
				check_quotes(tags, line, lineno)
			results.append((fo.name, tags))

	width_filename = max(0, *(len(x[0]) for x in results))
	all_tags = sorted(
		functools.reduce(
			lambda x, y: x | y,
			(x[1] for x in results)
		),
		key=tag_sort_order
	)
	width_tag =  max(0, *(len(x) for x in all_tags))
	for name, tags in results:
		for glob, skip_tags in opts.skip:
			if glob_match(name, glob) and (not skip_tags ^ {"*"} or not tags ^ skip_tags):
				break
		else:
			print(
				name.ljust(width_filename),
				"|",
				" ".join(
					map(
						lambda x: x.ljust(width_tag),
						(tag if tag in tags else "" for tag in all_tags)
					)
				)
			)


def glob_match(name, glob):
	name = pathlib.PurePath("/") / name
	if fnmatch.fnmatch(name, glob):
		return True

	possible_glob_suffix = "*" if glob.endswith("/") else "/*"

	if glob.startswith("/"):
		if fnmatch.fnmatch(name, glob + possible_glob_suffix):
			return True
	else:
		if fnmatch.fnmatch(name, "*/" + glob):
			return True
		if fnmatch.fnmatch(name, "*/" + glob + possible_glob_suffix):
			return True
	return False


def tag_sort_order(tag):
	if tag == "tabs":
		return (0, tag)
	elif tag == "spaces":
		return (1, tag)
	elif tag == "double":
		return (2, tag)
	elif tag == "single":
		return (3, tag)
	else:
		return (4, tag)


spaces_only = re.compile(r"^ +[^\s]")
tabs_only = re.compile(r"^\t+( \*\s*)?[^\s]")
tabs_or_spaces = re.compile(r"^\s+[^\s]")


def check_indentions(tags, line, filename, lineno):
	new_tags = set()
	if spaces_only.match(line):
		new_tags.add("spaces")
	elif tabs_only.match(line):
		new_tags.add("tabs")
	elif tabs_or_spaces.match(line):
		new_tags.add("mixed")
	tags |= new_tags


currently_in_multiline_comment = False
def check_quotes(tags, line, lineno):
	global currently_in_multiline_comment
	if currently_in_multiline_comment:
		comment_end = line.find("*/")
		if comment_end < 0:
			return
		currently_in_multiline_comment = False
		line = line[comment_end + 2:]
	else:
		comment_start = line.find("/*")
		if comment_start >= 0:
			check_quotes(tags, line[:comment_start], lineno)
			currently_in_multiline_comment = True
			check_quotes(tags, line[comment_start + 2:], lineno)
			return

	comment_start = line.find("//")
	if comment_start >= 0:
		line = line[:comment_start]

	if "\"" in line:
		tags.add("double")
	if "'" in line:
		tags.add("single")


def _parse_args(argv):
	parser = argparse.ArgumentParser(
		prog=argv[0],
		description=None,
		epilog=None
	)
	parser.add_argument(
		"--since", "-s",
		dest="since",
		metavar="GIT-COMMIT-ISH",
		type=str,
		default=None,
		help=(
			"show only files that has changes since the common "
			"ancestor of the HEAD and specified commit-ish"
		),
	)
	parser.add_argument(
		"--skip", "-k",
		dest="skip",
		metavar="GLOB=TAGS",
		action="append",
		type=parse_skip_argument,
		default=[],
		help=(
			"do not show files that have exactly the specified tag set, "
			"separate tags by spaces or commas"
		)
	)
	parser.add_argument(
		"--verbose", "-v",
		dest="verbose",
		action="store_true",
		default=False,
	)
	return parser.parse_args(argv[1:])


def parse_skip_argument(x):
	file_glob, tags = x.split("=", 1)
	tags = re.split(r"[\s,;]+", tags) if tags else []
	return (file_glob, set(tags))


if __name__ == '__main__':
	try:
		sys.exit(main(sys.argv))
	except KeyboardInterrupt:
		print(file=sys.stderr)
