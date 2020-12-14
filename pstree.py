#!/usr/bin/env python3

import sys, argparse, locale, subprocess, os, datetime, time, collections, re, json, pathlib


def main(*, args, prog):
	opts = parse_args(args=args, prog=prog)
	locale.setlocale(locale.LC_ALL, "")

	ANSI_smcup = "\x1b[?1049h"
	ANSI_rmcup = "\x1b[?1049l"
	ANSI_clear = "\x1b[H\x1b[2J"

	max_width = os.get_terminal_size().columns if sys.stdout.isatty() else 0

	def render():
		return "\n".join(
			p.render(
				exclude_pids=opts.exclude_pids,
				include_users=opts.include_users,
				exclude_users=opts.exclude_users,
				include_commands=opts.include_commands,
				exclude_commands=opts.exclude_commands,
				max_width=max_width
			)
				for p in gen_process_trees()
		)

	if opts.watch:
		try:
			sys.stdout.write(ANSI_smcup)
			while True:
				s = render()
				sys.stdout.write(ANSI_clear)
				sys.stdout.write("{}\n\n".format(datetime.datetime.now()))
				sys.stdout.write(s)
				sys.stdout.flush()
				time.sleep(opts.interval)
		except KeyboardInterrupt:
			pass
		finally:
			sys.stdout.write(ANSI_rmcup)
	else:
		output = render()
		sys.stdout.write(output)
		return 0 if output else 1


FIELD_NAME_PADDING = ("{", "}")


def encode_field_name(name):
	repcount = 20
	return FIELD_NAME_PADDING[0] * repcount + name + FIELD_NAME_PADDING[1] * repcount


def gen_process_trees():
	fields = [
		("pid", "pid"),
		("ppid", "ppid"),
		("pgid", "pgid"),
		("user", "user"),
		("etime", "etime"),
		("rss", "rss"),
		("args", "args") # must be last
	]
	ps_args = []
	if "sunos" not in sys.platform:
		fields.insert(-1, ("lstart", "lstart"))
	ps_args.extend(f"-o{kw}={encode_field_name(name)}" for name, kw in fields)
	ps_kwargs = dict(shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	with subprocess.Popen(["ps", "-e", *ps_args], **ps_kwargs) as p:
		ps_pid = p.pid
		stdout, stderr = p.communicate()
		retcode = p.wait()
		if retcode:
			raise subprocess.CalledProcessError(retcode, p.args, output=stdout, stderr=stderr)
		assert not stderr, stderr
		lines = stdout.decode().splitlines()
		max_width = max(len(l) for l in lines)

	def is_column_separator(offset):
		for l in lines:
			if len(l) - 1 < offset or not l[offset].isspace():
				return False
		return True

	columns = []

	begin = 0
	end = begin
	while end <= max_width:
		while begin < max_width and is_column_separator(begin):
			begin += 1
		end = begin
		while end <= max_width and not is_column_separator(end):
			end += 1
		columns.append((begin, end))
		begin = end

	#TODO:vruyr:bugs The padding string FIELD_NAME_PADDING is a sequence, not a set of chars. Also the padding must be stripped only from header.
	lines = [[l[begin:end].strip().lstrip(FIELD_NAME_PADDING[0]).rstrip(FIELD_NAME_PADDING[1]) for begin, end in columns] for l in lines]
	header = lines.pop(0)
	processes = [tuple((header[i], v) for i, v in enumerate(l)) for l in lines]

	tree_nodes = collections.defaultdict(TreeNode)
	for p in (dict(p) for p in processes):
		pid, ppid = p["pid"], p["ppid"]
		if int(pid) == ps_pid:
			continue
		node = tree_nodes[pid]
		node.data = p
		if ppid != pid:
			parent = tree_nodes[ppid]
			if parent.is_blank():
				parent.data = {"pid": ppid}
			parent.children.append(node)
			node.parent = parent

	yield from (n for n in tree_nodes.values() if n.parent is None)


class AnsiEscapeCode(str):
	pass


class TreeNode(object):
	__slots__ = ("data", "parent", "children", "_field_cache")

	indent = 4
	vertical = "│├└"
	horizontal = "─┬"
	style_lines = "\x1b[2;34m"
	style_pid   = "\x1b[2;35m"
	style_pgid  = "\x1b[2;34m"
	style_cmd   = "\x1b[37m"
	style_reset = "\x1b[0m"

	def __init__(self, *, data=None):
		self.data = None
		self.parent = None
		self.children = []
		self._field_cache = {}

	def __str__(self):
		return self.render()

	def get_style(self, name):
		code = getattr(self, "style_" + name, None)
		return AnsiEscapeCode(code) if code is not None else ""

	def is_blank(self):
		return not self.data

	def has_children(self):
		return len(self.children) > 0

	def get_field(self, name):
		return self.data.get(name) if self.data else None

	@property
	def etime(self):
		if "etime" not in self._field_cache:
			etime = self.get_field("etime")
			m = re.match(r"^(?:(\d+)-)?(?:(\d+):)?(?:(\d+):)?(?:(\d+))$", etime)
			if m is not None:
				days, hours, minutes, seconds = (int(x or 0) for x in m.groups())
				self._field_cache["etime"] = datetime.timedelta(
					days=days,
					hours=hours,
					minutes=minutes,
					seconds=seconds,
				)
			else:
				self._field_cache["etime"] = None
		return self._field_cache["etime"]

	@property
	def rss(self):
		return self.get_field("rss")

	@property
	def start_time(self):
		if "lstart" not in self._field_cache:
			lstart = self.get_field("lstart")
			if lstart is not None:
				self._field_cache["lstart"] = datetime.datetime.strptime(lstart, "%c")
			elif self.etime is not None:
				#TODO:vruyr:bugs Relative time should be calculated from a single point - the `ps` process.
				self._field_cache["lstart"] = datetime.datetime.now() - self.etime
			else:
				self._field_cache["lstart"] = datetime.datetime.fromtimestamp(0)
		return self._field_cache["lstart"]

	@property
	def pid(self):
		if "pid" not in self._field_cache:
			pid = self.get_field("pid")
			assert pid is not None, self.data
			self._field_cache["pid"] = int(pid) if pid is not None else None
		return self._field_cache["pid"]

	@property
	def ppid(self):
		if "ppid" not in self._field_cache:
			ppid = self.get_field("ppid")
			self._field_cache["ppid"] = int(ppid) if ppid is not None else None
		return self._field_cache["ppid"]

	@property
	def pgid(self):
		if "pgid" not in self._field_cache:
			pgid = self.get_field("pgid")
			self._field_cache["pgid"] = int(pgid) if pgid is not None else None
		return self._field_cache["pgid"]

	@property
	def user(self):
		return self.get_field("user")

	@property
	def args(self):
		return self.get_field("args")

	def render(self, *,
		max_width=None,
		exclude_pids=None,
		include_users=None,
		exclude_users=None,
		include_commands=None,
		exclude_commands=None,
	):
		result = ""
		width = max_width
		for piece in self.render_gen(
			exclude_pids=exclude_pids,
			include_users=include_users,
			exclude_users=exclude_users,
			include_commands=include_commands,
			exclude_commands=exclude_commands
		):
			if isinstance(piece, AnsiEscapeCode) or not max_width:
				result += str(piece)
			elif piece == "\n":
				width = max_width
				result += piece
			else:
				piece = str(piece)
				result += piece[:width]
				width -= len(piece)
		return result

	def indent_self(self, *, has_parent, has_siblings_after, has_children):
		if not has_parent:
			return ""
		return (
			self.vertical[1 if has_siblings_after else 2] +
			self.horizontal[0] * (self.indent - 1) +
			self.horizontal[1 if has_children else 0] +
			" "
		)

	def indent_child(self, *, has_uncles_after):
		return (
			(self.vertical[0] if has_uncles_after else " ") +
			" " * (self.indent - 1)
		)

	@staticmethod
	def matches_one_of_regexes(s, regexes):
		if s is None:
			return False
		for r in regexes:
			if re.match(r, s):
				return True
		return False

	def render_gen(self, *,
		exclude_pids=None,
		include_users=None,
		exclude_users=None,
		include_commands=None,
		exclude_commands=None,
		has_siblings_after=False,
		_indent="",
		_has_parent=False,
	):
		include_users = set(include_users) if include_users else include_users

		if (
			(exclude_pids and self.pid in exclude_pids)
			# or
			# (exclude_commands and self.matches_one_of_regexes(self.args, exclude_commands))
		):
			return

		#TODO:vruyr:bugs Simplify the inclusion and exclusion selection logic.

		def is_included():
			return (
				(not (include_users or include_commands)) or
				(include_users and (self.user in include_users)) or
				(include_commands and self.matches_one_of_regexes(self.args, include_commands))
			)

		def is_excluded():
			return (
				(exclude_users and self.user in exclude_users) or
				(exclude_commands and self.matches_one_of_regexes(self.args, exclude_commands))
			)

		explicitely_included = is_included() and not is_excluded()

		def render_children():
			renderings = []
			for node in self.children:
				r = list(node.render_gen(
					exclude_pids=exclude_pids,
					include_users=include_users,
					exclude_users=exclude_users,
					include_commands=include_commands,
					exclude_commands=exclude_commands,
					has_siblings_after=True,
					_indent=(_indent + self.indent_child(has_uncles_after=has_siblings_after) if _has_parent else _indent),
					_has_parent=True,
				))
				if r:
					renderings.append((node, r))
			for n, r in renderings[:-1]:
				yield from r
			#TODO:vruyr:design Instead of re-rendering the last child, start from the end first
			if renderings:
				yield from renderings[-1][0].render_gen(
					exclude_pids=exclude_pids,
					include_users=include_users,
					exclude_users=exclude_users,
					include_commands=include_commands,
					exclude_commands=exclude_commands,
					has_siblings_after=False,
					_indent=(_indent + self.indent_child(has_uncles_after=has_siblings_after) if _has_parent else _indent),
					_has_parent=True,
				)


		children_rendering = list(render_children())
		if explicitely_included or children_rendering:
			yield self.get_style("lines")
			yield _indent
			yield self.indent_self(has_parent=_has_parent, has_siblings_after=has_siblings_after, has_children=bool(children_rendering))
			yield self.get_style("reset")
			yield from self.render_self()
			yield "\n"
			yield from children_rendering

	def render_self(self):
		if self.is_blank():
			yield "(blank)"
			return
		yield self.get_style("pid")
		yield "{}".format(self.pid)
		yield self.get_style("reset")
		yield " "
		yield self.get_style("pgid")
		yield "(PGID: {})".format(self.pgid)
		yield self.get_style("reset")
		yield " "
		yield self.rss
		yield " "
		yield self.get_style("user")
		yield self.user
		yield self.get_style("reset")
		yield " "
		yield self.get_style("cmd")
		yield self.args
		yield self.get_style("reset")


def parse_args(*, args, prog, _args_file_already_loaded=False):
	parser = argparse.ArgumentParser(prog=prog)
	parser.add_argument(
		"--watch", "-w", dest="watch", action="store_true", default=False,
		help="update until interrupted"
	)
	parser.add_argument(
		"--interval", "-n", dest="interval", action="store", metavar="SECONDS", type=float, default=1.0,
		help="seconds to wait between updates"
	)
	parser.add_argument(
		"--args-file", "-a", dest="args_file", action="store", metavar="JSON_FILE_PATH", type=pathlib.Path, default=None,
		help="prepend all arguments loaded from specified json file to ones provided on command_line"
	)
	parser.add_argument(
		"--user", "-u", dest="include_users", action="append", metavar="USERNAME", type=str,
		help="only show process subtrees that has specified user"
	)
	parser.add_argument(
		"--not-user", "-U", dest="exclude_users", action="append", metavar="USERNAME", type=str,
		help="only show processes for specified user or its ancestors"
	)
	parser.add_argument(
		"--not-pid", "-P", dest="exclude_pids", action="append", metavar="PID", type=int, default=[],
		help="excludes process subtrees starting from specified PID"
	)
	parser.add_argument(
		"--command", "-c", dest="include_commands", action="append", metavar="REGEX", type=str, default=[],
		help="only include processes whose commands are matching specified regular expressions"
	)
	parser.add_argument(
		"--not-command", "-C", dest="exclude_commands", action="append", metavar="REGEX", type=str, default=[],
		help="only include processes whose commands are not matching specified regular expressions"
	)
	opts = parser.parse_args(args)
	opts.exclude_pids = [os.getpid() if pid == -1 else pid for pid in opts.exclude_pids]
	if opts.args_file and not _args_file_already_loaded:
		with opts.args_file.open("r") as fo:
			prepend_args = json.load(fo)
		return parse_args(args=[*prepend_args, *args], prog=prog, _args_file_already_loaded=True)
	return opts


if __name__ == "__main__":
	sys.exit(main(args=sys.argv[1:], prog=sys.argv[0]))
