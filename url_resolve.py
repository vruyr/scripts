#!/usr/bin/env python3

import sys, argparse, urllib.parse, collections, urllib.request, html.parser


def main(argv=None):
	opts = parse_args(argv=argv)
	urls = collections.deque(opts.urls)
	while urls:
		url = urls.popleft()
		if url == "-":
			urls.extendleft(map(str.rstrip, sys.stdin.readlines()[::-1]))
			continue
		opener = urllib.request.build_opener()
		opener.addheaders = [
			("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.7 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.7")
		]
		response = opener.open(url)
		url = strip_url(response.geturl())
		charset = response.headers.get_param("charset")
		body = response.read().decode(charset if isinstance(charset, str) else "utf-8")
		parser = TitleExtractorHtmlParser()
		parser.feed(body)
		sys.stdout.buffer.write("".join(parser.titles).strip().encode("utf-8"))
		sys.stdout.buffer.write("\n".encode())
		sys.stdout.buffer.write(url.encode("utf-8"))
		sys.stdout.buffer.write("\n".encode())


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
	remove = [
		"utm_source",
		"utm_medium",
		"utm_campaign",
		"utm_term",
		"ncid",
		"?ncid"
	]
	for r in remove:
		if r in query:
			del query[r]
	query = urllib.parse.urlencode(query, doseq=True, safe="?")
	url = urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))
	return url


def parse_args(argv=None):
	parser = argparse.ArgumentParser(prog=argv[0], description=None, epilog=None)
	parser.add_argument("urls", action="store", nargs="+", metavar="URL")
	opts = parser.parse_args(argv[1:])
	return opts


if __name__ == "__main__":
	try:
		sys.exit(main(sys.argv))
	except KeyboardInterrupt:
		print(file=sys.stderr)
