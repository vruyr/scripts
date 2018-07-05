#!/usr/bin/env python3

"""
Usage:
    {prog} (--airport=<airport>)... [--time=<time>]
    {prog} --help
    {prog} --version

Options:
    --airport, -a <airport>  Name, IATA/FAA, or ICAO code of the airport to lookup.
    --time, -t <time>        Date and time in the airport local timezone to calculate.
                             Please note that the timezone provided in this parameter is ignored.
                             [default: now]
"""


# Python 3.6.5
import sys, csv, urllib.request, cgi, json, datetime
# pip install docopt==0.6.2
import docopt
# pip install python-dateutil==2.7.3
import dateutil.parser, dateutil.tz


# TODO Use https://openflights.org/data.html to give options of entering airport code instead of timezone.


__prog__ = "airport-lookup.py"
__product__ = f"The {json.dumps(__prog__)} Script"
__version__ = "0.0.0"


def main(*, args):
	params = docopt.docopt(
		doc=__doc__.format(
			prog=__prog__,
		),
		argv=args,
		help=True,
		version=__version__,
		options_first=False,
	)
	print(params)
	assert params.pop("--help") == False
	assert params.pop("--version") == False
	lookup_airports = params.pop("--airport")
	lookup_time = params.pop("--time")
	assert not params, params

	airpots_data_url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
	airpots_data_fieldnames = [
		"id", "name", "city", "country", "iata/faa", "icao", "latitude", "longitude",
		"elevation", "utcoffset", "unknown_field_1", "timezone", "type", "database",
	]

	with urllib.request.urlopen(airpots_data_url) as fo:
		contentType, contentTypeOptions = cgi.parse_header(fo.info()["Content-Type"])
		assert contentType == "text/plain", contentType
		charset = contentTypeOptions.pop("charset")
		assert not contentTypeOptions, contentTypeOptions
		airports = fo.read().decode(charset)

	if lookup_time == "now":
		lookup_time = datetime.datetime.now()
	else:
		lookup_time = dateutil.parser.parse(lookup_time)

	result = []

	reader = csv.DictReader(airports.splitlines(), fieldnames=airpots_data_fieldnames)
	for a in reader:
		for lookup_airport in lookup_airports:
			if lookup_airport not in (a["name"], a["iata/faa"], a["icao"]):
				continue
			a["datetime"] = "{:%Y-%m-%dT%H:%M:%S%z}".format(
				lookup_time.replace(tzinfo=dateutil.tz.gettz(a["timezone"]))
			)
			result.append(a)

	print(json.dumps(result, indent="\t"))


if __name__ == "__main__":
	sys.exit(main(args=sys.argv[1:]))
