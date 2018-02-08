#!/usr/bin/env python3

import sys, argparse, urllib.parse, collections, urllib.request, html.parser, json


def main(argv=None):
	opts = parse_args(argv=argv)
	urls = collections.deque(opts.urls)
	encoding = "utf-8"
	while urls:
		url = urls.popleft()
		if url == "-":
			urls.extendleft(map(str.rstrip, sys.stdin.readlines()[::-1]))
			continue
		opener = urllib.request.build_opener()
		opener.addheaders = [
			# ("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.7 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.7")
			("User-Agent", "curl/7.43.0")
		]
		response = opener.open(url)
		resolved_url = strip_url(response.geturl())
		charset = response.headers.get_param("charset")
		body = response.read().decode(charset if isinstance(charset, str) else encoding)
		parser = TitleExtractorHtmlParser()
		parser.feed(body)
		title = "".join(parser.titles).strip()
		if opts.format in ("simple",):
			sys.stdout.write(title)
			sys.stdout.write("\n")
			sys.stdout.write(resolved_url)
			sys.stdout.write("\n")
		elif opts.format in ("taskpaper", "task", "t"):
			sys.stdout.write("-\t")
			sys.stdout.write(title)
			sys.stdout.write("\n\t")
			sys.stdout.write(resolved_url)
			sys.stdout.write("\n")
		elif opts.format in ("json",):
			sys.stdout.write(json.dumps({
				"title": title,
				"url": url,
				"resolved_url": resolved_url,
			}, indent="\t"))
			sys.stdout.write("\n")
		else:
			raise ValueError("unrecognized output format - " + repr(opts.format))


class TitleExtractorHtmlParser(html.parser.HTMLParser):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__capture_title = False
		self.__titles = []

	def handle_starttag(self, tag, attrs):
		if tag.lower() != "title":
			return
		self.__capture_title = True

	def handle_endtag(self, tag):
		if tag.lower() != "title":
			return
		self.__capture_title = False

	def handle_data(self, data):
		if not self.__capture_title:
			return
		self.__titles.append(data)

	def handle_entityref(self, name):
		if not self.__capture_title:
			return
		self.__titles.append(html.unescape("&%s;" % name))

	def handle_charref(self, name):
		if not self.__capture_title:
			return
		self.__titles.append(html.unescape("&#%s;" % name))

	@property
	def titles(self):
		return self.__titles


def strip_url(url):
	urlparts = urllib.parse.urlparse(url)
	scheme, netloc, path, params, query, fragment = urlparts
	query = urllib.parse.parse_qs(query)
	netloc_parts = netloc.partition(":")

	remove_from_all = [
		"utm_source",
		"utm_medium",
		"utm_campaign",
		"utm_term",
		"ncid",
		"?ncid"
	]
	for r in remove_from_all:
		if r in query:
			del query[r]

	if netloc_parts[0] == "www.youtube.com" or netloc_parts[0] == "youtube.com":
		if query.get("feature") == ["youtu.be"]:
			del query["feature"]

	query = urllib.parse.urlencode(query, doseq=True, safe="?")
	url = urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))
	return url


def parse_args(argv=None):
	parser = argparse.ArgumentParser(prog=argv[0], description=None, epilog=None)
	parser.add_argument("urls", action="store", metavar="URL", nargs="+")
	parser.add_argument("--format", "-f", action="store", metavar="FORMAT",
		choices=[
			"simple",
			"taskpaper", "task", "t",
			"json",
		],
		default="taskpaper",
	)
	opts = parser.parse_args(argv[1:])
	return opts


if __name__ == "__main__":
	try:
		sys.exit(main(sys.argv))
	except KeyboardInterrupt:
		print(file=sys.stderr)
