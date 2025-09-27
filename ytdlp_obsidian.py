#!/usr/bin/env python3

import datetime, json, re


def format_ytdlp_entry_for_obsidian(entry):
	del entry["automatic_captions"]
	del entry["chapters"]
	del entry["formats"]
	del entry["meta_description"]
	del entry["requested_downloads"]
	del entry["requested_formats"]
	del entry["thumbnails"]
	del entry["tags"]

	md = []

	upload_date = datetime.datetime.strptime(entry["upload_date"], "%Y%m%d")
	md.append("> [!YouTube]- ")
	md.append(f"`{entry["id"]}` ")
	md.append(f"{upload_date.strftime("%Y-%m-%d")} [")
	md.append(entry["title"])
	md.append("](")
	md.append(entry["webpage_url"])
	md.append(") (")
	md.append(format_seconds(entry["duration"]))
	md.append(") ")
	md.append("by [")
	md.append(entry["uploader"])
	md.append("](")
	md.append(entry["uploader_url"])
	md.append(")")
	md.append("\n")
	md.append(markdown_blockquote(entry["description"], escape=True))

	return "".join(md)


def markdown_escape(text):
	return re.sub(r"([\`*_{}\[\]()#+\-!|>~])", r"\\\1", text)


def markdown_blockquote(text, escape=True):
	lines = []
	for line in text.splitlines():
		line = line.strip()
		if not line:
			continue
		if escape:
			line = markdown_escape(line)
		lines.append("> " + line)
	return "\n".join(lines)


def format_seconds(seconds):
	h = seconds // 3600
	m = (seconds % 3600) // 60
	s = seconds % 60
	if h > 0:
		return f"{h}:{m:02}:{s:02}"
	else:
		return f"{m:02}:{s:02}"


if __name__ == "__main__":
	import sys
	if len(sys.argv) != 2:
		print("Usage: python ytdlp_obsidian.py <json_file>")
		sys.exit(1)

	json_file = sys.argv[1]
	if json_file == "-":
		entry = json.load(sys.stdin)
	else:
		with open(json_file, "r") as f:
			entry = json.load(f)

	print(format_ytdlp_entry_for_obsidian(entry))
