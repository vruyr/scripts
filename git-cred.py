#!/usr/bin/env python3

"""
Usage:
	{prog} URL
"""

import sys, asyncio, subprocess, os
# pip install 'docopt>=0.6.2'
import docopt


async def amain(*, args, prog):
	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	url = params.pop("URL")
	assert not params, params

	log = asyncio.Queue()
	pending_tasks = []
	printer_task = asyncio.create_task(
		printer(queue=log, fo=sys.stdout)
	)

	git = Git(output_queue=log, git_path="git")

	out = await git.credential("fill", {
		"url": url,
	})
	await log.put(out)

	await asyncio.gather(*pending_tasks)
	current_task, all_tasks = (asyncio.current_task(), asyncio.all_tasks())
	assert {current_task, printer_task} == all_tasks, (current_task, all_tasks)

	await log.put(None)
	await printer_task


class Git(object):
	def __init__(self, *, output_queue, git_path, encoding="UTF-8"):
		self._output = output_queue
		self._git_path = git_path
		self._encoding = encoding

	async def cmd(self, *args, stdin_data=None):
		if isinstance(stdin_data, str):
			stdin_data = stdin_data.encode(self._encoding)
		elif stdin_data is None:
			stdin_data = b""
		assert isinstance(stdin_data, bytes)

		env = dict(os.environ)
		env["GIT_TERMINAL_PROMPT"] = "0"
		env["GIT_ASKPASS"] = "true"

		p = await asyncio.create_subprocess_exec(
			self._git_path, *args,
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			start_new_session=True,
			env=env
		)
		stdout_bytes, stderr_bytes = await p.communicate(input=stdin_data)
		assert isinstance(stdout_bytes, bytes) and isinstance(stderr_bytes, bytes), (stdout_bytes, stderr_bytes)
		if stderr_bytes:
			raise RuntimeError(f"git command {args} produced stderr output - {stderr_bytes}")
		return stdout_bytes

	async def credential(self, cmd, params):
		stdin = "".join(f"{name}={value}\n" for  name, value in params.items())
		out = await self.cmd("credential", "fill", stdin_data=stdin)
		out = out.decode(self._encoding)
		return dict(p.split("=", 1) for p in out.splitlines(keepends=False))

	async def config(self, *args):
		out = await self.cmd("config", *args)
		return out.decode(self._encoding)


async def printer(*, queue, fo):
	while True:
		item = await queue.get()
		if item is None:
			break
		if isinstance(item, (list, tuple)):
			print(*item, file=fo)
		else:
			print(item, file=fo)


def main(argv=None):
	if argv is None:
		argv = sys.argv

	try:
		if sys.platform == "win32":
			asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

		return asyncio.run(amain(
			args=argv[1:],
			prog=argv[0]
		))
	except KeyboardInterrupt:
		print(file=sys.stderr)


if __name__ == "__main__":
	sys.exit(main())
