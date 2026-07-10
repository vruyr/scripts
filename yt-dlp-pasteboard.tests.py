#!/bin/sh
"exec" "uv" "--quiet" "run" "--no-project" "--script" "--" "$0" "$@"
# https://peps.python.org/pep-0723/
# https://github.com/astral-sh/uv
# /// script
# requires-python = ">=3.12,<4"
# dependencies = [
#   "textual >=3,<8",
# ]
# ///

__doc__ = """
Headless tests for yt-dlp-pasteboard.py; run this file directly.

Covers URL validation, argument parsing, the URL audit log, and the real
TUI driven by Textual's test pilot against a fake yt-dlp — this same file
invoked with --fake-ytdlp, which speaks the marker protocol (TITLE/PROG/
PP/DEST on stdout) and fails a controllable number of times based on
keywords in the URL.
"""

import sys, os, time, json, hashlib


def fake_ytdlp():
	url = sys.argv[-1]
	digest = hashlib.md5(url.encode()).hexdigest()[:6]

	# Attempt counter, persisted per URL so retries can be simulated.
	state_file = os.path.join(os.environ["FAKE_STATE_DIR"], digest)
	attempt = int(open(state_file).read()) if os.path.exists(state_file) else 0
	attempt += 1
	with open(state_file, "w") as fo:
		fo.write(str(attempt))

	fail_attempts = 0
	if "fail-once" in url:
		fail_attempts = 1
	elif "always-fail" in url:
		fail_attempts = 10**9

	print(f"TITLE\tVideo {digest}", flush=True)

	if attempt <= fail_attempts:
		print("WARNING: something benign", file=sys.stderr, flush=True)
		print(f"ERROR: transient failure on attempt {attempt}", file=sys.stderr, flush=True)
		sys.exit(1)

	if "already-have" in url:
		print(f"[download] Video {digest} has already been downloaded", flush=True)
		return

	total = 1_000_000
	total_field = "NA" if "no-total" in url else total
	stream_files = [f"Video {digest}.f616.mp4"]
	if "two-streams" in url:
		stream_files.append(f"Video {digest}.f251.webm")
	for stream_file in stream_files:
		for i in range(0, 11):
			print(f"PROG\t{i * total // 10}\t{total_field}\tNA\t250000.0\t{10 - i}\t{json.dumps(stream_file)}", flush=True)
			time.sleep(0.02)
	print("PP\tstarted", flush=True)
	print("PP\tfinished", flush=True)
	print(f"DEST\t{json.dumps(f'/downloads/Video {digest}.mp4')}", flush=True)


if "--fake-ytdlp" in sys.argv:
	fake_ytdlp()
	sys.exit(0)


import asyncio, importlib.util, tempfile

TESTS_PATH = os.path.abspath(__file__)
SCRIPT_PATH = os.path.join(os.path.dirname(TESTS_PATH), "yt-dlp-pasteboard.py")

spec = importlib.util.spec_from_file_location("pbtui", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

failures = []


def check(condition, label):
	print(("PASS" if condition else "FAIL"), label)
	if not condition:
		failures.append(label)


# --- URL validation ---

check(mod.is_downloadable_url("https://www.youtube.com/watch?v=abc"), "url: plain https accepted")
check(not mod.is_downloadable_url("not a url"), "url: prose rejected")
check(not mod.is_downloadable_url("ftp://host/x"), "url: non-http scheme rejected")
check(not mod.is_downloadable_url("https://"), "url: no host rejected")
check(not mod.is_downloadable_url("line1\nhttps://x.com/"), "url: multi-line rejected")


# --- argument parsing ---

opts = mod.parse_args(args=["--yt-dlp", "yt-dlp", "--", "--config-locations", "~/.config/yt-dlp/x"], prog="t")
check(opts["yt_dlp"] == "yt-dlp", "args: --yt-dlp stored")
check(opts["ytdlp_args"] == ["--config-locations", "~/.config/yt-dlp/x"], "args: forwarding after --")
check(mod.parse_args(args=[], prog="t")["ytdlp_args"] == [], "args: no -- means no extra args")
check(mod.parse_args(args=[], prog="t")["log_urls"] is None, "args: --log-urls defaults to None")
check(mod.parse_args(args=["--log-urls", "/tmp/u.log"], prog="t")["log_urls"] == "/tmp/u.log", "args: --log-urls stored")


# --- URL audit log ---

async def test_url_log():
	log_path = os.path.join(tempfile.mkdtemp(), "urls.log")

	async def source():
		for url in ["https://a.com/x", "https://a.com/x", "https://a.com/y"]:
			yield url

	passed_through = [url async for url in mod.tee_urls_to_log(source(), log_path)]
	lines = open(log_path, encoding="utf-8").read().splitlines()
	check(passed_through == ["https://a.com/x", "https://a.com/x", "https://a.com/y"], "log: URLs passed through unchanged")
	check(len(lines) == 3, f"log: all URLs logged incl. duplicates (got {len(lines)})")
	check(all(len(line.split("\t")) == 2 for line in lines), "log: tab-separated timestamp and URL")
	check(lines[0].split("\t")[1] == "https://a.com/x", "log: URL recorded verbatim")
	timestamp = lines[0].split("\t")[0]
	check("T" in timestamp, "log: timestamp looks ISO-8601")
	import datetime
	parsed = datetime.datetime.fromisoformat(timestamp)
	check(parsed.microsecond % 1000 == 0 and "." in timestamp, "log: timestamp has milliseconds")

asyncio.run(test_url_log())


# --- middle truncation ---

check(mod.truncate_middle("short.mp4", 20) == "short.mp4", "trunc: short text unchanged")
truncated = mod.truncate_middle("A Very Long Video Title With Format.f616.mp4", 20)
check(
	len(truncated) == 20 and "…" in truncated and truncated.startswith("A Very") and truncated.endswith(".mp4"),
	f"trunc: middle ellipsis keeps head and tail (got {truncated!r})",
)
check(mod.truncate_middle("abcdefghij", 5) == "ab…ij", "trunc: exact budget split")
check(mod.truncate_middle("abcdefghij", 1) == "…", "trunc: degenerate budget")


# --- sticky field widths ---

field_widths = mod.FieldWidths()
check(field_widths.pad("speed", "1.2 MiB/s") == "1.2 MiB/s", "widths: first value unpadded")
check(field_widths.pad("speed", "999.9 KiB/s") == "999.9 KiB/s", "widths: column grows with wider value")
check(field_widths.pad("speed", "1.2 MiB/s") == "  1.2 MiB/s", "widths: sticky width, right-aligned")
check(field_widths.pad("eta", "0:05") == "0:05", "widths: fields tracked independently")


# --- full app, headless ---

URLS = [
	"https://example.com/ok",
	"https://example.com/fail-once",
	"https://example.com/always-fail",
	"https://example.com/no-total",
	"https://example.com/two-streams",
	"https://example.com/already-have",
	"https://example.com/ok",  # duplicate, must be ignored
]
EXPECTED_ROWS = 6


async def url_source(queue):
	while (url := await queue.get()) is not None:
		yield url


async def run_app_test():
	os.environ["FAKE_STATE_DIR"] = tempfile.mkdtemp()
	queue = asyncio.Queue()
	for url in URLS:
		queue.put_nowait(url)
	notify_log = os.path.join(tempfile.mkdtemp(), "notify.log")
	app = mod.PasteboardDownloadApp(
		url_source=url_source(queue),
		command=(sys.executable, TESTS_PATH, "--fake-ytdlp"),
		extra_args=(),
		notify_command=(
			'printf \'%s\\t%s\\t%s\\t%s\\t%s\\n\' "$NOTIFY_EVENT" "$NOTIFY_URL"'
			' "$NOTIFY_TITLE" "$NOTIFY_ERROR" "$NOTIFY_ATTEMPT"'
			f' >> {notify_log}'
		),
	)
	terminal = {mod.DownloadState.DONE, mod.DownloadState.FAILED}
	info = {"seen_stream_files": set(), "status_samples": []}
	async with app.run_test(size=(100, 40)) as pilot:
		for _ in range(600):
			await pilot.pause(0.05)
			for row in app.rows:
				if "two-streams" in row.url:
					info["seen_stream_files"] |= set(row._file_lines.keys())
					if row.title and row.state is mod.DownloadState.DOWNLOADING and "downloading_title" not in info:
						info["downloading_title"] = str(row.query_one(".title", mod.Static).render())
				for line in row._file_lines.values():
					try:
						status = line.query_one(".file-status", mod.Static)
					except Exception:
						continue
					text = str(status.render())
					if text.strip():
						info["status_samples"].append((text, status.size.width))
			if len(app.rows) == EXPECTED_ROWS and all(row.state in terminal for row in app.rows):
				break
		info["row_margin"] = app.rows[0].styles.padding.bottom
		info["numbers_before_clear"] = [row.number for row in app.rows]
		done_row = next(row for row in app.rows if row.url.endswith("/ok"))
		info["done_title"] = str(done_row.query_one(".title", mod.Static).render())
		await pilot.press("c")
		await pilot.pause(0.1)
		# Textual's is_mounted does not flip back on removal; check the DOM.
		info["on_screen"] = {id(row): row.parent is not None for row in app.rows}
		failed_row = next(row for row in app.rows if "always-fail" in row.url)
		info["failed_number_after_clear"] = failed_row.number
		info["rows_before_late"] = len(app.rows)
		queue.put_nowait("https://example.com/late")
		for _ in range(100):
			await pilot.pause(0.05)
			if len(app.rows) == EXPECTED_ROWS + 1:
				break
		info["late_number"] = app.rows[-1].number
		# Notify commands run as fire-and-forget workers; wait for all
		# expected events (2 per clean download, +1 per extra attempt).
		for _ in range(100):
			await pilot.pause(0.05)
			if len(read_notify_log(notify_log)) >= 17 and all(
				row.state in terminal for row in app.rows
			):
				break
		# Re-queue an already-finished URL: no new row, but an
		# already-downloaded notification for the phone.
		queue.put_nowait("https://example.com/ok")
		for _ in range(100):
			await pilot.pause(0.05)
			if len(read_notify_log(notify_log)) >= 18:
				break
		info["rows_after_done_duplicate"] = len(app.rows)
	info["notify_events"] = read_notify_log(notify_log)
	return app, info


def read_notify_log(path):
	if not os.path.exists(path):
		return []
	lines = open(path, encoding="utf-8").read().splitlines()
	return [tuple(line.split("\t")) for line in lines]


app, info = asyncio.run(run_app_test())
on_screen = info["on_screen"]
seen_stream_files = info["seen_stream_files"]
row_margin = info["row_margin"]
S = mod.DownloadState
rows = {row.url.rsplit("/", 1)[-1]: row for row in app.rows}

check(info["rows_before_late"] == EXPECTED_ROWS, f"app: duplicate ignored, {EXPECTED_ROWS} rows (got {info['rows_before_late']})")
check(rows["ok"].state is S.DONE, "app: ok -> DONE")
check(rows["ok"].title and rows["ok"].title.startswith("Video "), "app: title captured")
check(rows["ok"].filepaths and rows["ok"].filepaths[0].endswith(".mp4"), "app: final filepath captured")
check(rows["fail-once"].state is S.DONE, "app: fail-once -> DONE after retry")
check(rows["fail-once"].attempt == 2, f"app: fail-once succeeded on attempt 2 (got {rows['fail-once'].attempt})")
check(rows["always-fail"].state is S.FAILED, "app: always-fail -> FAILED")
check(rows["always-fail"].attempt == mod.RETRY_COUNT, "app: always-fail used all retries")
check("transient failure" in (rows["always-fail"].error or ""), f"app: error captured from stderr (got {rows['always-fail'].error!r})")
check(rows["no-total"].state is S.DONE, "app: unknown-total download -> DONE")
check(rows["two-streams"].state is S.DONE, "app: two-streams -> DONE")
check(rows["already-have"].state is S.DONE, "app: already-have -> DONE")
check(rows["already-have"].already_downloaded, "app: already_downloaded flag set")
check(not rows["already-have"].filepaths, "app: already-have wrote no files")
check(len(seen_stream_files) == 2, f"streams: separate bar per file (saw {seen_stream_files})")
check(any(".f616." in name for name in seen_stream_files), "streams: video format code in bar label")
check(any(".f251." in name for name in seen_stream_files), "streams: audio format code in bar label")
check(not rows["two-streams"]._file_lines, "streams: bars cleared once DONE")
check(row_margin == 1, f"layout: blank line between rows (padding {row_margin})")
check(
	info["status_samples"]
	and all(mod.cell_len(text) == width and not text.endswith(" ") for text, width in info["status_samples"]),
	f"layout: stats flush right ({len(info['status_samples'])} samples)",
)
check(info["numbers_before_clear"] == [1, 2, 3, 4, 5, 6], f"numbers: sequential (got {info['numbers_before_clear']})")
check(info["failed_number_after_clear"] == 1, f"numbers: reset after clear (got {info['failed_number_after_clear']})")
check(info["late_number"] == 2, f"numbers: continue after reset (got {info['late_number']})")
check("Video " in info["done_title"] and "https://example.com/ok" in info["done_title"], f"done view: original URL after title (got {info['done_title']!r})")
check(
	"Video " in info.get("downloading_title", "") and "https://example.com/two-streams" in info.get("downloading_title", ""),
	f"downloading view: URL stays after title (got {info.get('downloading_title')!r})",
)
# The late row finishes after the snapshot and is legitimately on screen.
check(
	all(not on_screen[id(row)] for row in app.rows if id(row) in on_screen and row.state is S.DONE),
	"clear: DONE rows removed from screen",
)
check(on_screen[id(rows["always-fail"])], "clear: FAILED row still on screen")
check(len(app.rows) == EXPECTED_ROWS + 1, "clear: cleared rows kept for exit summary")


# --- notify command events ---

def events_for(url_suffix):
	url = f"https://example.com/{url_suffix}"
	return [event for event in info["notify_events"] if event[1] == url]

ok_events = events_for("ok")
check(
	[event[0] for event in ok_events] == ["started", "finished", "already-downloaded"],
	f"notify: ok -> started, finished, then already-downloaded for the re-queue (got {[e[0] for e in ok_events]})",
)
check(ok_events[2][2].startswith("Video "), f"notify: done-duplicate carries title (got {ok_events[2][2]!r})")
check(info["rows_after_done_duplicate"] == EXPECTED_ROWS + 1, "notify: done-duplicate adds no row")
already_events = events_for("already-have")
check(
	[event[0] for event in already_events] == ["started", "already-downloaded"],
	f"notify: already-have -> started, already-downloaded (got {[e[0] for e in already_events]})",
)
check(len(events_for("late")) and ok_events[0][2] == "", "notify: started has no title yet")
check(ok_events[1][2].startswith("Video "), f"notify: finished carries title (got {ok_events[1][2]!r})")
fail_once_events = events_for("fail-once")
check(
	[event[0] for event in fail_once_events] == ["started", "retrying", "finished"],
	f"notify: fail-once -> started, retrying, finished (got {[e[0] for e in fail_once_events]})",
)
check(fail_once_events[1][4] == "2", f"notify: retrying carries attempt number (got {fail_once_events[1][4]!r})")
always_fail_events = events_for("always-fail")
check(
	[event[0] for event in always_fail_events] == ["started"] + ["retrying"] * (mod.RETRY_COUNT - 1) + ["failed"],
	f"notify: always-fail -> started, retrying…, failed (got {[e[0] for e in always_fail_events]})",
)
check("transient failure" in always_fail_events[-1][3], f"notify: failed carries error (got {always_fail_events[-1][3]!r})")
check(len(info["notify_events"]) == 18, f"notify: no events for still-active duplicate URL (got {len(info['notify_events'])})")

print()
if failures:
	print(f"{len(failures)} FAILED")
	sys.exit(1)
print("ALL PASS")
