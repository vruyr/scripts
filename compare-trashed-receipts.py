#!/usr/bin/env python3

# Python Standard Library
import sys; assert sys.version_info[:2] in [(3, 7)]
import asyncio, subprocess, os, pathlib, shlex


async def main(*, args, prog, loop=None):
	home_dir = pathlib.Path.home()
	mwattachments_dir = home_dir / ".xgit/mwattachments"
	trash_dirs = [
		home_dir / ".Trash",
		home_dir / "Library/Mobile Documents/com~apple~CloudDocs/.Trash",
	]
	ignored_file_names = (
		".DS_Store",
	)
	max_parallel_tasks = 10

	mwattachments_files = {}
	for blob in (await git("-C", home_dir / mwattachments_dir, "ls-tree", "-r", "-z", "refs/heads/master")).split("\0"):
		if not blob:
			continue
		blob_info, filename = blob.split("\t")
		blob_mode, blob_type, blob_hash = blob_info.split(" ")
		assert blob_mode == "100644"
		assert blob_type == "blob"
		mwattachments_files[blob_hash] = filename

	trashed_file_names = []
	for trash_dir in trash_dirs:
		for fn in os.listdir(trash_dir):
			if fn in ignored_file_names:
				continue
			trashed_file_names.append(os.fspath(trash_dir / fn))

	num_trashed_files = len(trashed_file_names)

	trashed_files = {}

	async def hash_trashed_file(trashed_file):
		result = await git("hash-object", "-t", "blob", trashed_file)
		trashed_files[trashed_file] = result.strip()

	pending = set()
	while trashed_file_names or pending:
		num_tasks_needed = max_parallel_tasks - len(pending)
		if num_tasks_needed and trashed_file_names:
			pending.update(set(
				asyncio.ensure_future(hash_trashed_file(f))
					for f in trashed_file_names[:num_tasks_needed]
			))
			trashed_file_names = trashed_file_names[num_tasks_needed:]
		dummy_done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

	assert num_trashed_files == len(trashed_files), (num_trashed_files, trashed_files)

	num_committed_files = 0
	not_committed_files = []
	for fn, h in trashed_files.items():
		if h in mwattachments_files:
			num_committed_files += 1
			continue
		not_committed_files.append(fn)
	if not_committed_files:
		print(f"{num_committed_files} of {num_trashed_files} trashed files were committed to", mwattachments_dir)
		print("The following files are not committed to", mwattachments_dir)
		print("\t" + "\n\t".join(shlex.quote(fn) for fn in not_committed_files))
	else:
		print(f"All {num_committed_files} trashed files were committed to", mwattachments_dir)


async def git(*args):
	p = await asyncio.create_subprocess_exec(
		"git", *(str(a) for a in args),
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
	)
	stdout, stderr = await p.communicate()
	if stderr:
		raise RuntimeError(f"git command failed - {args} - {stderr}")
	return stdout.decode("utf-8")


def _smain(*, argv):
	try:
		if sys.platform == "win32":
			loop = asyncio.ProactorEventLoop()
			asyncio.set_event_loop(loop)
		else:
			loop = asyncio.get_event_loop()
		loop.run_until_complete(main(args=argv[1:], prog=argv[0], loop=loop))
	except KeyboardInterrupt:
		print(file=sys.stderr)


if __name__ == "__main__":
	sys.exit(_smain(argv=sys.argv))
