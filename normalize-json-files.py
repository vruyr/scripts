#!/usr/bin/env python3

"""
Usage:
	{prog}
"""

import sys, locale, asyncio, subprocess, os, json
# pip install docopt==0.6.2
import docopt


async def main(*, args, prog):
	locale.setlocale(locale.LC_ALL, "")

	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	assert not params, params

	log = asyncio.Queue()
	pending_tasks = []
	printer_task = asyncio.create_task(
		printer(queue=log, fo=sys.stdout)
	)


	all_files = [os.path.join(dirpath, fn) for dirpath, dirnames, filenames in os.walk(".") for fn in filenames]
	all_files_len = len(all_files)
	print(all_files_len)
	print()
	for i, filepath in enumerate(all_files):
		normalize_json_file(filepath)
		print("\x1b[1F\x1b[2K" + f"{i}/{all_files_len} = {100*i/all_files_len}")


	await asyncio.gather(*pending_tasks)
	current_task = asyncio.current_task()
	all_tasks = asyncio.all_tasks()
	assert {current_task, printer_task} == all_tasks, (current_task, all_tasks)

	await log.put(None)
	await printer_task


def normalize_json_file(filepath):
	with open(filepath, "r") as fo:
		data = json.load(fo)
	with open(filepath, "w") as fo:
		json.dump(data, fo, sort_keys=True, indent="\t")


async def printer(*, queue, fo):
	while True:
		item = await queue.get()
		if item is None:
			break
		if isinstance(item, (list, tuple)):
			print(*item, file=fo)
		else:
			print(item, file=fo)


def smain(argv=None):
	if argv is None:
		argv = sys.argv

	try:
		if sys.platform == "win32":
			asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

		return asyncio.run(
			main(
				args=argv[1:],
				prog=argv[0]
			),
			debug=False,
		)
	except KeyboardInterrupt:
		print(file=sys.stderr)


if __name__ == "__main__":
	sys.exit(smain())
