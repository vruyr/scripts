#!/usr/bin/env python
import sys, argparse, asyncio, subprocess
assert sys.version_info[:2] == (3, 5), "Python 3.5 only!"


async def main(*, argv=None, loop=None):
	opts = _parse_args(argv=argv)
	xx = (await pacman(opts.host, "-Qg")).decode().splitlines()
	# groups repeat - dict is not a good collection for this
	groups = dict(tuple(reversed(x.split(maxsplit=2))) for x in xx)
	packages = set((await pacman(opts.host, "-Qqtte")).decode().splitlines())
	result = {}
	while packages:
		p = packages.pop()
		if p in groups:
			result.setdefault(groups[p], list()).append(p)
		else:
			result[p] = None

	for p, c in sorted(result.items()):
		print(p)
		while c or []:
			x = c[:10]
			print(" " * 4, ", ".join(x))
			c = c[10:]



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
