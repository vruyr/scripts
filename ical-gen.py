#!/usr/bin/env python3

"""
Usage:
    {prog} START_DT_WITH_TIMEZONE END_DT_WITH_TIMEZONE [--summary=TEXT] [--description=TEXT]
        [--attachment=PATH]... [--url=URL] [--output=PATH]
    {prog} --help
    {prog} --version

Options:
    -s, --summary=TEXT      Summary
                            [default: Event]
    -d, --description=TEXT  Description
    -u, --url=URL           URL
    -a, --attachment=PATH   Path to a file to attach to the calendar event.
    -o, --output=PATH       Path to the file to be written.
                            [default: ./event.ics]
"""


# Python 3.6.5
import sys, os, datetime, json, mimetypes, urllib.request, base64
# pip install icalendar==4.0.1
import icalendar
# pip install docopt==0.6.2
import docopt
# pip install python-dateutil==2.7.2
import dateutil.parser


# TODO Use https://openflights.org/data.html to give options of entering airport code instead of timezone.


__prog__ = "ical-gen.py"
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
	assert params.pop("--help") == False
	assert params.pop("--version") == False
	dtstart = parse_dt(params.pop("START_DT_WITH_TIMEZONE"))
	dtend = parse_dt(params.pop("END_DT_WITH_TIMEZONE"))
	summary = params.pop("--summary") or "Event"
	description = params.pop("--description") or f"Generated By: {__product__}"
	url = params.pop("--url")
	attachments = params.pop("--attachment")
	output_path = params.pop("--output")
	assert not params, params

	print("Summary:     {}"      .format(summary))
	print("Start:       {:%c %z}".format(dtstart))
	print("End:         {:%c %z}".format(dtend))
	print("Duration:    {}"      .format(dtend - dtstart))
	print("Description: {}"      .format(description))
	print(file=sys.stderr)

	event = icalendar.Event()
	event.add("SUMMARY", icalendar.vText(summary))
	event.add("DESCRIPTION", icalendar.vText(description))
	event.add("DTSTART", icalendar.vDatetime(dtstart))
	event.add("DTEND", icalendar.vDatetime(dtend))
	if url is not None:
		event.add("URL", icalendar.vUri(url))
	for path in attachments:
		add_attachment_to_calendar_event(event, path)
	calendar = icalendar.Calendar()
	#TODO:vruyr:bugs Verify with the standard.
	calendar.add("PRODID", f"-//{__product__}//vruyr.com//EN")
	calendar.add("VERSION", "2.0")
	calendar.add_component(event)

	with open(output_path, "wb") as fo:
		fo.write(calendar.to_ical())


def add_attachment_to_calendar_event(event, path):
	mtype, dummy_encoding = mimetypes.MimeTypes().guess_type(urllib.request.pathname2url(path))
	assert mtype is not None
	with open(path, "rb") as fo:
		filebytes = fo.read()
	#TODO:vruyr:bugs The vBinary() seems to do a roundtrip encoding to and from unicode which
	#                might corrupt the data.
	#                See https://github.com/collective/icalendar/issues/205
	b = icalendar.prop.vInline(base64.b64encode(filebytes).decode("ascii"))
	b.params["VALUE"] = "BINARY"
	b.params["ENCODING"] = "BASE64"
	b.params["FMTTYPE"] = mtype
	#TODO:vruyr:bugs What is the standard way to set the filename?
	b.params["X-APPLE-FILENAME"] = os.path.basename(path)
	event.add("ATTACH", b, encode=False)


def parse_dt(dt_s):
	dt = dateutil.parser.parse(dt_s)
	dt = dt.replace(tzinfo=datetime.timezone(dt.tzinfo.utcoffset(dt)))
	return dt


if __name__ == "__main__":
	sys.exit(main(args=sys.argv[1:]))
