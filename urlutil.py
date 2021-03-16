#!/usr/bin/env python3

"""
Usage:
	{prog} [options] (--decompose | --compose) (--stdin | URL_OR_JSON)

Options:
	--stdin          Read the input from standard input.
	--decompose, -d  Convert a URL into JSON object
	--compose, -c    Convert a JSON object into URL
"""

import sys, locale, os, urllib.parse, json, collections
# pip install docopt==0.6.2
import docopt


DEFAULT_ENCODING = "UTF-8"


def main(*, args, prog):
	locale.setlocale(locale.LC_ALL, "")

	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	url_or_json = params.pop("URL_OR_JSON")
	if params.pop("--stdin"):
		url_or_json = sys.stdin.read()
	if params.pop("--decompose"):
		assert not params.pop("--compose")
		must_decompose = True
		the_url = url_or_json
	else:
		assert params.pop("--compose")
		must_decompose = False
		the_json = url_or_json
	del url_or_json
	assert not params, params

	if must_decompose:
		sys.stdout.write(decompose(the_url))
	else:
		sys.stdout.write(compose(the_json))


def decompose(the_url):
	scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(the_url)
	if query:
		query = collections.OrderedDict(urllib.parse.parse_qsl(
			query,
			keep_blank_values=True,
			strict_parsing=True,
			encoding=DEFAULT_ENCODING,
			errors="strict",
		))
	return json.dumps(
		collections.OrderedDict((
			("scheme",   scheme),
			("netloc",   netloc),
			("path",     path),
			("params",   params),
			("query",    query),
			("fragment", fragment),
		)),
		indent="\t",
	)


def compose(the_json):
	the_json = json.loads(
		the_json,
		object_pairs_hook=collections.OrderedDict
	)
	scheme   = the_json.pop("scheme")
	netloc   = the_json.pop("netloc")
	path     = the_json.pop("path")
	params   = the_json.pop("params")
	query    = the_json.pop("query")
	fragment = the_json.pop("fragment")
	assert not the_json
	query = urllib.parse.urlencode(
		query,
		doseq=False,
		safe="",
		encoding=DEFAULT_ENCODING,
		errors="strict",
		quote_via=urllib.parse.quote
	)
	return urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))


def smain(argv=None):
	if argv is None:
		argv = sys.argv

	try:
		return main(
			args=argv[1:],
			prog=argv[0]
		)
	except KeyboardInterrupt:
		print(file=sys.stderr)


if __name__ == "__main__":
	sys.exit(smain())
