#!/bin/sh
"exec" "uv" "--quiet" "run" "--no-project" "--script" "--" "$0" "$@"
# vim: ft=python ts=4 sw=4 noet:
# https://peps.python.org/pep-0723/
# https://github.com/astral-sh/uv
# /// script
# requires-python = ">=3.14,<4"
# dependencies = [
#   "aiohttp >=3.12.14",
# ]
# ///

__doc__ = """
Headless tests for readwisereader; run this file directly.

Covers argument parsing, the ANSI hyperlink helper, and the
ReadwiseReaderClient driven against a fake in-process Readwise API
(aiohttp test server) — saving new documents, appending notes when a
URL already exists, update field validation, paginated tag listing,
and the main() command dispatch.
"""

import sys, os, io, json, asyncio, contextlib, importlib.machinery, importlib.util, pathlib, tempfile

from aiohttp import web
from aiohttp.test_utils import TestServer

TESTS_PATH = os.path.abspath(__file__)
SCRIPT_PATH = os.path.join(os.path.dirname(TESTS_PATH), "readwisereader")

loader = importlib.machinery.SourceFileLoader("readwisereader", SCRIPT_PATH)
spec = importlib.util.spec_from_loader("readwisereader", loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

failures = []


def check(condition, label):
	print(("PASS" if condition else "FAIL"), label)
	if not condition:
		failures.append(label)


def raises(exc_type, fn):
	try:
		fn()
	except exc_type:
		return True
	except BaseException:
		return False
	return False


def araises(exc_type, coro):
	return raises(exc_type, lambda: asyncio.run(coro))


async def araises_in_loop(exc_type, coro):
	try:
		await coro
	except exc_type:
		return True
	except BaseException:
		return False
	return False


# --- argument parsing ---

def parse(args):
	return mod.parse_args(args=args, prog="t")


def parse_exits(args):
	with contextlib.redirect_stderr(io.StringIO()):
		return raises(SystemExit, lambda: parse(args))


opts = parse(["save", "-t", "foo", "-t", "bar", "-n", "n1", "-n", "n2", "-l", "later", "https://example.com/1", "https://example.com/2"])
check(opts["command"] == "save", "args: save command selected")
check(opts["urls"] == ["https://example.com/1", "https://example.com/2"], "args: positional URLs collected")
check(opts["tags"] == ["foo", "bar"], "args: repeated --tag appended")
check(opts["notes"] == ["n1", "n2"], "args: repeated --notes appended")
check(opts["location"] == "later", "args: --location stored")

opts = parse(["save", "https://example.com/1"])
check(opts["tags"] is None and opts["notes"] is None and opts["location"] is None, "args: save options default to None")

check(parse(["tags"]) == {"command": "tags"}, "args: tags command has no extra options")

check(parse_exits([]), "args: command is required")
check(parse_exits(["save"]), "args: save requires at least one URL")
check(parse_exits(["bogus"]), "args: unknown command rejected")
check(parse_exits(["save", "--location", "sofa", "https://example.com/1"]), "args: invalid location rejected")
check(parse_exits(["tags", "--tag", "foo"]), "args: tags rejects save-only options")


# --- ANSI hyperlink helper ---

check(
	mod.ansi_hyperlink(text="doc1", url="https://read.example/doc1") == "\x1b]8;;https://read.example/doc1\x07doc1\x1b]8;;\x07",
	"hyperlink: OSC 8 escape sequence",
)


# --- client outside of `async with` ---

bare = mod.ReadwiseReaderClient(access_token="x")
check(araises(RuntimeError, bare.save(url="https://example.com/")), "client: save outside async-with raises")
check(araises(RuntimeError, bare.fetch_tags()), "client: fetch_tags outside async-with raises")
check(araises(RuntimeError, bare.get_document(document_id="d")), "client: get_document outside async-with raises")
check(araises(RuntimeError, bare.update_document(document_id="d", title="t")), "client: update_document outside async-with raises")


# --- fake Readwise API ---

class FakeReadwiseAPI:
	def __init__(self, *, tag_pages):
		self.documents = {}
		self.tag_pages = tag_pages
		self.save_requests = []
		self.update_requests = []
		self.tag_cursors = []

	def add_document(self, *, source_url, notes=""):
		doc_id = f"doc{len(self.documents) + 1}"
		doc = {
			"id": doc_id,
			"source_url": source_url,
			"url": f"https://read.example/{doc_id}",
			"notes": notes,
		}
		self.documents[doc_id] = doc
		return doc

	async def handle_save(self, request):
		payload = await request.json()
		self.save_requests.append({
			"authorization": request.headers.get("Authorization"),
			"payload": payload,
		})
		existing = next((d for d in self.documents.values() if d["source_url"] == payload["url"]), None)
		if existing:
			return web.json_response({"id": existing["id"], "url": existing["url"]}, status=200)
		doc = self.add_document(source_url=payload["url"], notes=payload.get("notes", ""))
		return web.json_response({"id": doc["id"], "url": doc["url"]}, status=201)

	async def handle_list(self, request):
		doc = self.documents.get(request.query.get("id"))
		results = [doc] if doc else []
		return web.json_response({"count": len(results), "results": results})

	async def handle_update(self, request):
		doc_id = request.match_info["doc_id"]
		payload = await request.json()
		self.update_requests.append({"id": doc_id, "payload": payload})
		self.documents[doc_id].update(payload)
		return web.json_response(self.documents[doc_id])

	async def handle_tags(self, request):
		cursor = request.query.get("pageCursor")
		self.tag_cursors.append(cursor)
		index = int(cursor) if cursor else 0
		next_cursor = str(index + 1) if index + 1 < len(self.tag_pages) else None
		return web.json_response({
			"count": sum(len(page) for page in self.tag_pages),
			"nextPageCursor": next_cursor,
			"results": self.tag_pages[index],
		})


@contextlib.asynccontextmanager
async def fake_api(*, tag_pages=()):
	api = FakeReadwiseAPI(tag_pages=list(tag_pages))
	app = web.Application()
	app.router.add_post("/save/", api.handle_save)
	app.router.add_get("/list/", api.handle_list)
	app.router.add_patch("/update/{doc_id}/", api.handle_update)
	app.router.add_get("/tags/", api.handle_tags)
	server = TestServer(app)
	await server.start_server()
	try:
		mod.ReadwiseReaderClient.DOC_CREATE_URL = str(server.make_url("/save/"))
		mod.ReadwiseReaderClient.DOC_LIST_URL = str(server.make_url("/list/"))
		mod.ReadwiseReaderClient.DOC_UPDATE_URL = str(server.make_url("/update/"))
		mod.ReadwiseReaderClient.TAG_LIST_URL = str(server.make_url("/tags/"))
		yield api
	finally:
		await server.close()


TAG_PAGES = [
	[{"key": "delta", "name": "delta"}, {"key": "alpha", "name": "alpha"}],
	[{"key": "gamma", "name": "gamma"}],
	[{"key": "beta", "name": "beta"}],
]


# --- client against the fake API ---

async def test_client():
	async with fake_api(tag_pages=TAG_PAGES) as api:
		async with mod.ReadwiseReaderClient(access_token="test-token") as client:
			# save: new document
			result = await client.save(url="https://example.com/a", tags=["t1", "t2"], notes="first note", location="later")
			check(result["id"] == "doc1" and result["url"] == "https://read.example/doc1", "save: created document returned")
			request = api.save_requests[-1]
			check(request["authorization"] == "Token test-token", "save: auth header sent")
			check(
				request["payload"] == {"url": "https://example.com/a", "tags": ["t1", "t2"], "notes": "first note", "location": "later"},
				f"save: full payload (got {request['payload']})",
			)

			# save: empty optionals omitted from payload
			await client.save(url="https://example.com/b", tags=[], notes="", location=None)
			check(api.save_requests[-1]["payload"] == {"url": "https://example.com/b"}, "save: empty tags/notes/location omitted")

			# save: duplicate URL without notes returns as-is, no update
			result = await client.save(url="https://example.com/a")
			check(result["id"] == "doc1", "save: duplicate without notes returns existing")
			check(len(api.update_requests) == 0, "save: duplicate without notes does not update")

			# save: duplicate URL with notes appends to existing notes
			result = await client.save(url="https://example.com/a", notes="second note")
			check(api.documents["doc1"]["notes"] == "first note\n\nsecond note", f"save: notes appended with blank line (got {api.documents['doc1']['notes']!r})")
			check(api.update_requests[-1] == {"id": "doc1", "payload": {"notes": "first note\n\nsecond note"}}, "save: update patches only notes")
			check(result["notes"] == "first note\n\nsecond note", "save: updated document returned")

			# save: duplicate whose existing notes are empty gets no leading separator
			await client.save(url="https://example.com/b", notes="solo")
			check(api.documents["doc2"]["notes"] == "solo", f"save: no separator before first note (got {api.documents['doc2']['notes']!r})")

			# get_document
			document = await client.get_document(document_id="doc1")
			check(document["id"] == "doc1" and document["source_url"] == "https://example.com/a", "get_document: fetched by id")

			# update_document validation
			check(await araises_in_loop(ValueError, client.update_document(document_id="doc1", bogus="x")), "update_document: unsupported field rejected")
			check(await araises_in_loop(ValueError, client.update_document(document_id="doc1")), "update_document: empty fields rejected")

			# fetch_tags pagination
			tags = await client.fetch_tags()
			check([tag["name"] for tag in tags] == ["delta", "alpha", "gamma", "beta"], f"tags: all pages collected in API order (got {[t['name'] for t in tags]})")
			check(api.tag_cursors == [None, "1", "2"], f"tags: cursor followed (got {api.tag_cursors})")


asyncio.run(test_client())


# --- main() dispatch ---

async def test_main():
	config_dir = pathlib.Path(tempfile.mkdtemp())
	with (config_dir / "auth.json").open("w") as fo:
		json.dump({"access_token": "test-token"}, fo)
	mod.CONFIG_DIR = config_dir

	async with fake_api(tag_pages=TAG_PAGES) as api:
		out = io.StringIO()
		with contextlib.redirect_stdout(out):
			await mod.main(command="tags")
		check(out.getvalue().splitlines() == ["alpha", "beta", "delta", "gamma"], "main: tags prints names sorted, one per line")

		out = io.StringIO()
		with contextlib.redirect_stdout(out):
			await mod.main(command="save", urls=["https://example.com/x"], tags=None, notes=["line1", "line2"], location=None)
		check(api.save_requests[-1]["payload"].get("notes") == "line1\nline2", "main: save joins notes with newline")
		line = out.getvalue().splitlines()[0]
		check("https://example.com/x" in line and "\x1b]8;;https://read.example/" in line, f"main: save prints hyperlink and URL (got {line!r})")

		with contextlib.redirect_stdout(io.StringIO()):
			await mod.main(command="save", urls=["https://example.com/y"], tags=None, notes=None, location=None)
		check("notes" not in api.save_requests[-1]["payload"], "main: save omits notes when none given")

	check(await araises_in_loop(NotImplementedError, mod.main(command="bogus")), "main: unknown command raises")


asyncio.run(test_main())


print()
if failures:
	print(f"{len(failures)} FAILED")
	sys.exit(1)
print("ALL PASS")
