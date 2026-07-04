#!/bin/sh
"exec" "uv" "--quiet" "run" "--no-project" "--script" "--" "$0" "$@"
# https://peps.python.org/pep-0723/
# https://github.com/astral-sh/uv
# /// script
# requires-python = ">=3.12,<4"
# dependencies = [
#   "textual >=3,<8",
#   "pyobjc-framework-Cocoa >=10; sys_platform == 'darwin'",
# ]
# ///

__doc__ = """
Watch the macOS pasteboard for URLs and download each one with yt-dlp,
showing per-download progress bars in a full-screen TUI.

Each copied URL gets a row in the UI; failed downloads are retried
automatically. Press c to clear successfully finished downloads from the
list. When the TUI exits (press q), a plain-text summary of successes and
failures is printed to stdout — including rows cleared from the screen.

Everything after "--" is forwarded to yt-dlp verbatim.
"""

import sys, os, locale, argparse, asyncio, dataclasses, datetime, enum, json, shlex, urllib.parse
from collections import deque

from rich.cells import cell_len
from rich.text import Text
from textual.app import App
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.widget import Widget
from textual.widgets import Footer, Header, ProgressBar, Static


RETRY_COUNT = 3
PASTEBOARD_POLL_INTERVAL_SECONDS = 0.25
STDERR_TAIL_LINES = 5

# Markers our yt-dlp invocation prints on stdout; everything else is ignored.
YTDLP_OUTPUT_ARGS = (
	"--newline",
	"--progress",
	"--no-quiet",  # --print implies --quiet, which would move progress lines to stderr
	"--no-simulate",  # --print implies --simulate
	"--progress-template", "download:PROG\t%(progress.downloaded_bytes)s\t%(progress.total_bytes)s\t%(progress.total_bytes_estimate)s\t%(progress.speed)s\t%(progress.eta)s\t%(progress.filename)j",
	"--progress-template", "postprocess:PP\t%(progress.status)s",
	"--print", "video:TITLE\t%(title)s",
	"--print", "after_move:DEST\t%(filepath)j",
)


async def main(
	*,
	# Options
	yt_dlp,
	watch_file,
	log_urls,
	ytdlp_args,
):
	locale.setlocale(locale.LC_ALL, "")

	command = tuple(shlex.split(yt_dlp))
	url_source = (
		watch_file_for_urls(watch_file) if watch_file is not None
		else watch_pasteboard_for_urls()
	)
	if log_urls is not None:
		url_source = tee_urls_to_log(url_source, log_urls)

	app = PasteboardDownloadApp(
		url_source=url_source,
		command=command,
		extra_args=tuple(ytdlp_args),
	)
	await app.run_async()

	failures = 0
	for row in app.rows:
		if row.state is DownloadState.DONE:
			for path in row.filepaths:
				print(f"✔ {path}")
			if not row.filepaths:
				print(f"✔ {row.title or row.url}")
		elif row.state is DownloadState.FAILED:
			failures += 1
			print(f"✘ {row.title or row.url} — {row.error}")
		else:
			failures += 1
			print(f"∅ {row.title or row.url} — interrupted")

	return 1 if failures else 0


# --- URL sources ------------------------------------------------------------


async def watch_pasteboard_for_urls():
	from AppKit import NSPasteboard, NSPasteboardTypeString

	pasteboard = NSPasteboard.generalPasteboard()
	last_change_count = pasteboard.changeCount()

	while True:
		await asyncio.sleep(PASTEBOARD_POLL_INTERVAL_SECONDS)
		change_count = pasteboard.changeCount()
		if change_count == last_change_count:
			continue
		last_change_count = change_count
		text = pasteboard.stringForType_(NSPasteboardTypeString)
		if text is None:
			continue
		text = text.strip()
		if is_downloadable_url(text):
			yield text


async def watch_file_for_urls(path):
	with open(path, "r", encoding="utf-8", errors="replace") as fo:
		while True:
			line = fo.readline()
			if not line:
				await asyncio.sleep(PASTEBOARD_POLL_INTERVAL_SECONDS)
				continue
			text = line.strip()
			if is_downloadable_url(text):
				yield text


async def tee_urls_to_log(source, path):
	with open(path, "a", encoding="utf-8") as fo:
		async for url in source:
			timestamp = datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")
			print(f"{timestamp}\t{url}", file=fo, flush=True)
			yield url


def is_downloadable_url(text):
	if not text or any(map(str.isspace, text)):
		return False
	try:
		parts = urllib.parse.urlsplit(text)
	except ValueError:
		return False
	return parts.scheme in ("http", "https") and bool(parts.netloc)


# --- Downloader -------------------------------------------------------------


@dataclasses.dataclass
class AttemptStarted:
	number: int

@dataclasses.dataclass
class TitleKnown:
	title: str

@dataclasses.dataclass
class Progress:
	downloaded: float
	total: float | None
	speed: float | None
	eta: float | None
	filename: str | None

@dataclasses.dataclass
class PostProcessing:
	pass

@dataclasses.dataclass
class FileWritten:
	filepath: str

@dataclasses.dataclass
class Finished:
	pass

@dataclasses.dataclass
class Failed:
	message: str


async def download_events(url, *, command, extra_args):
	"""Run yt-dlp for a single URL, retrying on failure, yielding events.

	The generator's finally block is await-free so that aclose() during
	cancellation completes synchronously and still kills the subprocess.
	"""
	stderr_tail = deque(maxlen=STDERR_TAIL_LINES)
	exit_code = None

	for attempt in range(1, RETRY_COUNT + 1):
		yield AttemptStarted(attempt)

		proc = await asyncio.create_subprocess_exec(
			*command, *YTDLP_OUTPUT_ARGS, *extra_args, "--", url,
			stdin=asyncio.subprocess.DEVNULL,
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.PIPE,
		)
		stderr_tail.clear()
		stderr_task = asyncio.create_task(read_lines_into_tail(proc.stderr, stderr_tail))
		try:
			async for event in parse_ytdlp_stdout(proc.stdout):
				yield event
			await stderr_task
			exit_code = await proc.wait()
		finally:
			stderr_task.cancel()
			if proc.returncode is None:
				proc.terminate()

		if exit_code == 0:
			yield Finished()
			return

	errors = [line for line in stderr_tail if "ERROR" in line]
	message = (errors or list(stderr_tail) or [f"yt-dlp exited with code {exit_code}"])[-1]
	yield Failed(message)


async def parse_ytdlp_stdout(stream):
	async for raw_line in stream:
		line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
		marker, _, rest = line.partition("\t")
		if marker == "TITLE":
			yield TitleKnown(rest)
		elif marker == "PROG":
			if (progress := parse_progress_line(rest)) is not None:
				yield progress
		elif marker == "PP":
			yield PostProcessing()
		elif marker == "DEST":
			try:
				yield FileWritten(json.loads(rest))
			except json.JSONDecodeError:
				pass


def parse_progress_line(rest):
	# The filename is JSON-encoded, so it cannot contain a literal tab.
	fields = rest.split("\t")
	if len(fields) != 6:
		return None
	downloaded, total, total_estimate, speed, eta = map(parse_optional_number, fields[:5])
	try:
		filename = json.loads(fields[5])
	except json.JSONDecodeError:
		filename = None
	return Progress(
		downloaded=downloaded or 0,
		total=total or total_estimate,
		speed=speed,
		eta=eta,
		filename=filename if isinstance(filename, str) else None,
	)


def parse_optional_number(text):
	try:
		return float(text)
	except ValueError:
		return None  # yt-dlp prints "NA" for unknown fields


async def read_lines_into_tail(stream, tail):
	async for raw_line in stream:
		line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
		if line:
			tail.append(line)


# --- UI ---------------------------------------------------------------------


class DownloadState(enum.Enum):
	QUEUED = enum.auto()
	DOWNLOADING = enum.auto()
	PROCESSING = enum.auto()
	DONE = enum.auto()
	FAILED = enum.auto()
	INTERRUPTED = enum.auto()


STATE_DECOR = {
	DownloadState.QUEUED: ("…", "dim"),
	DownloadState.DOWNLOADING: ("↓", "cyan"),
	DownloadState.PROCESSING: ("⚙", "yellow"),
	DownloadState.DONE: ("✔", "green"),
	DownloadState.FAILED: ("✘", "red"),
	DownloadState.INTERRUPTED: ("∅", "red"),
}


class FileProgressLine(Widget):
	"""One progress bar for one output file (e.g. the video stream, then the audio stream)."""

	DEFAULT_CSS = """
	FileProgressLine {
		height: 1;
		layout: horizontal;
		margin-left: 2;
	}
	FileProgressLine ProgressBar {
		width: auto;
	}
	FileProgressLine .file-status {
		width: 1fr;
		margin-left: 1;
		color: $text-muted;
		text-wrap: nowrap;
		text-overflow: ellipsis;
	}
	"""

	def __init__(self, filename):
		super().__init__()
		self.filename = filename
		self._progress = None

	def compose(self):
		yield ProgressBar(show_eta=False)
		yield Static(classes="file-status")

	def on_mount(self):
		self._refresh()

	def update_progress(self, progress):
		self._progress = progress
		if self.is_mounted:
			self._refresh()

	def freeze(self):
		try:
			bar = self.query_one(ProgressBar)
		except NoMatches:  # not composed yet, or being torn down
			return
		if bar.total is None:
			bar.update(total=100, progress=0)

	def on_resize(self):
		self._refresh()

	def _refresh(self):
		progress = self._progress
		if progress is None:
			return
		try:
			bar = self.query_one(ProgressBar)
			status_widget = self.query_one(".file-status", Static)
		except NoMatches:  # not composed yet, or being torn down
			return
		if progress.total:
			bar.update(total=progress.total, progress=progress.downloaded)
		else:
			bar.update(total=None)
		# ETA comes and goes between ticks; keep it leftmost so the fields
		# after it stay anchored to the right edge when it disappears.
		parts = []
		if progress.eta is not None:
			parts.append("ETA " + FIELD_WIDTHS.pad("eta", format_duration(progress.eta)))
		if progress.total:
			parts.append(
				FIELD_WIDTHS.pad("downloaded", format_bytes(progress.downloaded))
				+ " / "
				+ FIELD_WIDTHS.pad("total", format_bytes(progress.total))
			)
		else:
			parts.append(FIELD_WIDTHS.pad("downloaded", format_bytes(progress.downloaded)))
		if progress.speed:
			parts.append(FIELD_WIDTHS.pad("speed", f"{format_bytes(progress.speed)}/s"))
		stats = " · ".join(parts)
		available = status_widget.size.width
		if available <= 0:
			# Not laid out yet; on_resize re-renders once a width is known.
			return
		# Stats stay flush right; the filename absorbs the leftover space.
		name = os.path.basename(self.filename) if self.filename else ""
		if name:
			name = truncate_middle(name, max(5, available - cell_len(stats) - 1))
			gap = max(1, available - cell_len(name) - cell_len(stats))
			text = name + " " * gap + stats
		else:
			text = " " * max(0, available - cell_len(stats)) + stats
		status_widget.update(Text(text, no_wrap=True, overflow="ellipsis"))


class DownloadRow(Widget):
	DEFAULT_CSS = """
	DownloadRow {
		height: auto;
		layout: vertical;
		/* padding, not margin: the row owns and repaints this blank line,
		   so height changes cannot leave stale text behind in the gap */
		padding-bottom: 1;
	}
	DownloadRow > .title {
		height: 1;
		text-wrap: nowrap;
		text-overflow: ellipsis;
	}
	DownloadRow > .status {
		height: 1;
		margin-left: 2;
		color: $text-muted;
		text-wrap: nowrap;
		text-overflow: ellipsis;
	}
	"""

	def __init__(self, url, number):
		super().__init__()
		self.url = url
		self.number = number
		self.title = None
		self.filepaths = []
		self.state = DownloadState.QUEUED
		self.error = None
		self.attempt = 0
		self._file_lines = {}  # progress filename -> FileProgressLine

	def compose(self):
		yield Static(classes="title")
		yield Static(classes="status")

	def on_mount(self):
		for line in self._file_lines.values():
			if line.parent is None:
				self.mount(line)
		self.refresh_row()

	async def set_attempt(self, number):
		self.attempt = number
		if self.state is not DownloadState.QUEUED:
			self.state = DownloadState.QUEUED
			await self._clear_file_lines()
		self.refresh_row()

	def set_title(self, title):
		self.title = title
		self.refresh_row()

	async def set_progress(self, progress):
		self.state = DownloadState.DOWNLOADING
		key = progress.filename or ""
		line = self._file_lines.get(key)
		if line is None:
			line = FileProgressLine(key)
			self._file_lines[key] = line
			if self.is_mounted:
				await self.mount(line)
				self.request_full_repaint()
		line.update_progress(progress)
		self.refresh_row()

	def set_post_processing(self):
		self.state = DownloadState.PROCESSING
		self.refresh_row()

	def add_filepath(self, filepath):
		self.filepaths.append(filepath)
		self.refresh_row()

	async def set_done(self):
		self.state = DownloadState.DONE
		await self._clear_file_lines()
		self.refresh_row()

	def set_failed(self, message):
		self.state = DownloadState.FAILED
		self.error = message
		self._freeze_file_lines()
		self.refresh_row()

	def set_interrupted(self):
		self.state = DownloadState.INTERRUPTED
		self._freeze_file_lines()
		self.refresh_row()

	async def _clear_file_lines(self):
		lines = list(self._file_lines.values())
		self._file_lines.clear()
		for line in lines:
			if line.parent is not None:
				await line.remove()
		if lines:
			self.request_full_repaint()

	def request_full_repaint(self):
		"""Repaint the whole screen after a height change.

		Incremental repaints can leave stale lines behind when rows shift
		up or down, so flush everything whenever the layout grows/shrinks.
		"""
		try:
			self.screen.refresh()
		except Exception:  # detached or app shutting down
			pass

	def _freeze_file_lines(self):
		for line in self._file_lines.values():
			line.freeze()

	def refresh_row(self):
		if not self.is_mounted:
			return
		try:
			title_widget = self.query_one(".title", Static)
			status_widget = self.query_one(".status", Static)
		except NoMatches:  # is_mounted stays True after removal; children may be gone
			return

		icon, style = STATE_DECOR[self.state]
		title = Text(no_wrap=True, overflow="ellipsis")
		title.append(f"{icon} ", style)
		title.append(f"{self.number}. ")
		title.append(self.title or self.url)
		if self.title:
			title.append(f" — {self.url}", "dim")
		title_widget.update(title)

		match self.state:
			case DownloadState.QUEUED:
				status = "starting…"
			case DownloadState.DOWNLOADING:
				status = "downloading…"
			case DownloadState.PROCESSING:
				status = "post-processing…"
			case DownloadState.DONE:
				status = ", ".join(os.path.basename(p) for p in self.filepaths) or "done"
			case DownloadState.FAILED:
				status = self.error or "failed"
			case DownloadState.INTERRUPTED:
				status = "interrupted"
		if self.attempt > 1 and self.state in (
			DownloadState.QUEUED, DownloadState.DOWNLOADING, DownloadState.PROCESSING
		):
			status = f"[attempt {self.attempt}/{RETRY_COUNT}] {status}"
		status_widget.update(Text(status, no_wrap=True, overflow="ellipsis"))


class PasteboardDownloadApp(App):
	TITLE = "yt-dlp pasteboard watcher"
	BINDINGS = [
		Binding("q", "quit", "Quit"),
		Binding("c", "clear_finished", "Clear finished"),
	]
	CSS = """
	#downloads {
		padding: 0 1;
	}
	"""

	def __init__(self, *, url_source, command, extra_args):
		super().__init__()
		self._url_source = url_source
		self._command = command
		self._extra_args = extra_args
		self._next_number = 1
		self.rows = []
		self.sub_title = shlex.join([*command, *extra_args])

	def compose(self):
		yield Header()
		yield VerticalScroll(id="downloads")
		yield Footer()

	def on_mount(self):
		self.run_worker(self._watch_urls(), group="url-watcher")

	async def _watch_urls(self):
		async for url in self._url_source:
			if self._is_active_or_done(url):
				self.notify(f"Already handled: {url}", severity="warning")
				continue
			row = DownloadRow(url, number=self._next_number)
			self._next_number += 1
			self.rows.append(row)
			await self.query_one("#downloads").mount(row)
			row.scroll_visible()
			self.screen.refresh()
			self.run_worker(self._download(url, row), group="downloads")

	async def action_clear_finished(self):
		# Removes the widgets only; rows stay in self.rows for the exit summary.
		# is_mounted stays True after removal, so check DOM membership instead.
		for row in self.rows:
			if row.state is DownloadState.DONE and row.parent is not None:
				await row.remove()
		remaining = [row for row in self.rows if row.parent is not None]
		for number, row in enumerate(remaining, start=1):
			row.number = number
			row.refresh_row()
		self._next_number = len(remaining) + 1
		self.screen.refresh()

	def _is_active_or_done(self, url):
		return any(
			row.url == url and row.state not in (DownloadState.FAILED, DownloadState.INTERRUPTED)
			for row in self.rows
		)

	async def _download(self, url, row):
		events = download_events(url, command=self._command, extra_args=self._extra_args)
		try:
			async for event in events:
				match event:
					case AttemptStarted(number=number):
						await row.set_attempt(number)
					case TitleKnown(title=title):
						row.set_title(title)
					case Progress():
						await row.set_progress(event)
					case PostProcessing():
						row.set_post_processing()
					case FileWritten(filepath=filepath):
						row.add_filepath(filepath)
					case Finished():
						await row.set_done()
					case Failed(message=message):
						row.set_failed(message)
		except asyncio.CancelledError:
			row.set_interrupted()
			raise
		except Exception as exc:
			row.set_failed(f"internal error: {exc!r}")
		finally:
			await events.aclose()


class FieldWidths:
	"""Sticky column widths, shared by all rows.

	Once a field (speed, ETA, …) has been rendered at some width, narrower
	values are right-aligned into that width instead of shrinking it, so the
	stats text does not jitter left and right between updates or across rows.
	"""

	def __init__(self):
		self._widths = {}

	def pad(self, field, text):
		width = self._widths[field] = max(self._widths.get(field, 0), cell_len(text))
		return " " * (width - cell_len(text)) + text


FIELD_WIDTHS = FieldWidths()


def truncate_middle(text, max_cells):
	if cell_len(text) <= max_cells:
		return text
	if max_cells <= 1:
		return "…"
	budget = max_cells - 1
	head_budget = (budget + 1) // 2
	tail_budget = budget // 2
	head = ""
	width = 0
	for char in text:
		char_width = cell_len(char)
		if width + char_width > head_budget:
			break
		head += char
		width += char_width
	tail = ""
	width = 0
	for char in reversed(text):
		char_width = cell_len(char)
		if width + char_width > tail_budget:
			break
		tail = char + tail
		width += char_width
	return f"{head}…{tail}"


def format_bytes(num):
	if num is None:
		return "?"
	for unit in ("B", "KiB", "MiB", "GiB"):
		if num < 1024:
			return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
		num /= 1024
	return f"{num:.1f} TiB"


def format_duration(seconds):
	if seconds is None:
		return "?"
	hours, remainder = divmod(int(seconds), 3600)
	minutes, secs = divmod(remainder, 60)
	if hours:
		return f"{hours}:{minutes:02}:{secs:02}"
	return f"{minutes}:{secs:02}"


# --- Entry point ------------------------------------------------------------


def parse_args(*, args, prog):
	ytdlp_args = []
	if "--" in args:
		split_index = args.index("--")
		ytdlp_args = args[split_index + 1:]
		args = args[:split_index]

	parser = argparse.ArgumentParser(
		prog=prog,
		usage="%(prog)s [OPTIONS]... [-- YTDLP_ARGS...]",
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

	options_main = parser.add_argument_group("Main Options")
	options_main.add_argument(
		"--yt-dlp", metavar="COMMAND",
		action="store", dest="yt_dlp", default="uv tool run yt-dlp@latest",
		help="command used to run yt-dlp, parsed with shlex" + the_default,
	)
	options_main.add_argument(
		"--watch-file", metavar="PATH",
		action="store", dest="watch_file", default=None,
		help="read URLs appended to PATH instead of watching the macOS pasteboard\n(for testing on other platforms)",
	)
	options_main.add_argument(
		"--log-urls", metavar="PATH",
		action="store", dest="log_urls", default=None,
		help="append every accepted URL to PATH as \"<timestamp>\\t<url>\" lines\n(for audit purposes; duplicates are logged too)",
	)

	opts = vars(parser.parse_args(args))
	opts["ytdlp_args"] = ytdlp_args
	return opts


def smain(argv=None):
	if argv is None:
		argv = sys.argv

	try:
		opts = parse_args(args=argv[1:], prog=argv[0])
		return asyncio.run(
			main(**opts),
			debug=False,
		)
	except KeyboardInterrupt:
		print(file=sys.stderr)


if __name__ == "__main__":
	sys.exit(smain())
