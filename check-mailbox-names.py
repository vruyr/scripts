#!/usr/bin/env python3

import sys, locale, argparse, pathlib, collections, json, subprocess


CONFIG_DIR = pathlib.Path.home() / ".config" / pathlib.Path(__file__).stem


def main(
	*,
	# Example Options
	show_all_mailboxes: bool
) -> None:
	locale.setlocale(locale.LC_ALL, "")

	if show_all_mailboxes:
		for label, entries in list_accounts():
			print(label)
			for entry in sorted(entries, key=mailbox_name_sort_order_key):
				print("\t", "/".join(entry["path"]), sep="")
			print()
	else:
		folders = collections.defaultdict(list)
		ignored_paths = set(tuple(path) for path in read_config("ignore"))
		for label, entries in list_accounts():
			for entry in entries:
				path = entry["path"]
				if tuple(path) in ignored_paths:
					continue
				path.insert(0, label)
				for p in path:
					assert "/" not in p
				folders[path[-1]].append("/".join(path))

		folders = {name: paths for name, paths in folders.items() if len(paths) != 1}
		print("\n\n".join(
			"\n".join(paths) for paths in folders.values()
		))


the_mailbox_name_order_first = ["INBOX", "Drafts", "Sent", "Junk", "Spam", "Trash"]
the_mailbox_name_order_last = ["Archive"]
emojis = ["⏱", "📥", "🗃️"]
def mailbox_name_sort_order_key(entry):
	path = entry["path"]
	if path[0] == "[Gmail]":
		path = path[1:]
	for i in emojis:
		if path and path[0].startswith(i):
			order = (2, path)
			break
	else:
		order = (3, path)
	try:
		order = (1, the_mailbox_name_order_first.index(path[0]), *path)
	except:
		try:
			order = (4, the_mailbox_name_order_last.index(path[0]), *path)
		except:
			pass
	return order


def list_accounts():
	for label, url in read_config("accounts"):
		p = subprocess.run(
			["imap.py", "-a", url, "--json"],
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			shell=False
		)
		assert p.returncode == 0, p
		assert not p.stderr
		try:
			out = p.stdout.decode()
		except:
			print(p.stdout)
			raise
		try:
			out = json.loads(out)
		except:
			print(out)
			raise
		yield (label, out)


def read_config(name):
	with (CONFIG_DIR / (name + ".json")).open("r") as fo:
		return json.load(fo)


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
		"--show-all-mailboxes",
		action="store_true", dest="show_all_mailboxes", default=False, required=False,
		help="instead of finding mailboxes with same name, simply list all mailboxes in all accounts" + the_default
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
