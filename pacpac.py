#!/usr/bin/env python3
import sys, argparse, asyncio, subprocess
assert sys.version_info[:2] in [(3, 5), (3, 6)], "Incompatible python version."


async def main(*, argv=None, loop=None):
	opts = _parse_args(argv=argv)
	xx = (await pacman(opts.host, "-Qg")).decode().splitlines()

	complete_groups = dict()
	for x in xx:
		group, package = x.split(maxsplit=2)
		complete_groups.setdefault(group, list()).append(package)

	# groups repeat - dict is not a good collection for this
	package_to_group_map = dict(tuple(reversed(x.split(maxsplit=2))) for x in xx)
	packages = set((await pacman(opts.host, "-Qqtte")).decode().splitlines())
	item_to_constituents_map = {}
	while packages:
		p = packages.pop()
		if p in package_to_group_map:
			item_to_constituents_map.setdefault(package_to_group_map[p], list()).append(p)
		else:
			item_to_constituents_map[p] = None

	for item, content in sorted(item_to_constituents_map.items()):
		print(item)
		if content is None:
			continue

		show_wrapped(content, indent=4)

		not_installed = set(complete_groups[item]) - set(content)
		extra_installed = set(content) - set(complete_groups[item])

		if not_installed:
			print("\n    Not Installed:")
			show_wrapped(sorted(not_installed), indent=8)
			print()

		if extra_installed:
			print("\n    Extra Installed:")
			show_wrapped(sorted(extra_installed), indent=8)
			print()


def show_wrapped(array, *, indent=0, maxperline=10):
	if array is None:
		return

	if not isinstance(indent, str) and indent is not None:
		indent = indent * " "
	elif indent is None:
		indent = ""

	while array or []:
		x = array[:maxperline]
		print(indent + " ".join(x))
		array = array[maxperline:]


async def pacman(host, *argv):
	remote = ["ssh", host] if host is not None else []
	p = await asyncio.create_subprocess_exec(
		*remote, "pacman", *argv,
		stdout=subprocess.PIPE
	)
	stdout, _ = await p.communicate()
	return stdout


def _parse_args(argv=None):
	parser = argparse.ArgumentParser(
		prog=(argv[0] if argv is not None else None),
		description=None,
		epilog=None
	)
	parser.add_argument("host", nargs="?", metavar="SSH_HOST", type=str, default=None, help="")
	opts = parser.parse_args((argv[1:] if argv is not None else None))
	return opts


def _smain(*, argv=None):
	if sys.platform == 'win32':
		loop = asyncio.ProactorEventLoop()
		asyncio.set_event_loop(loop)
	else:
		loop = asyncio.get_event_loop()
	loop.run_until_complete(main(argv=argv, loop=loop))


if __name__ == "__main__":
	try:
		sys.exit(_smain())
	except KeyboardInterrupt:
		print(file=sys.stderr)
