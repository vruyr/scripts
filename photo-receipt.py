#!/usr/bin/env python3

# Python Standard Library
import sys; assert sys.version_info[:2] in [(3, 6)]
import asyncio, subprocess, json, re, datetime
# pip install timezonefinder>=3.0.1
import timezonefinder
# pip install python-dateutil>=2.7.2
import dateutil.tz


async def main(*, args, prog, loop=None):
	tzfinder = timezonefinder.TimezoneFinder()

	for photo_path in args:
		p = await asyncio.create_subprocess_exec(
			"exiftool", "-json", "-groupnames", "--printConv",
			photo_path,
			stdout=subprocess.PIPE,
		)
		stdout, stderr = await p.communicate()
		raw_data = json.loads(stdout.decode("utf-8"))
		for entry in raw_data:
			if entry["SourceFile"] != photo_path:
				continue
			latitude = entry["Composite:GPSLatitude"]
			longitude = entry["Composite:GPSLongitude"]
			m = re.match(r"(?P<year>\d{4}):(?P<month>\d{2}):(?P<day>\d{2}) (?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})", entry["EXIF:DateTimeOriginal"])
			tz = tzfinder.timezone_at(lat=latitude, lng=longitude)
			dt = datetime.datetime(
				**dict((k, int(v)) for k, v in m.groupdict().items()),
				tzinfo=dateutil.tz.gettz(tz),
			)

			result = "Transaction Date: {datetime:%Y-%m-%d %H:%M:%S %z}\nLocation: {latitude:.6f},{longitude:.6f}\nPayee: ?\nAccount: ?\nAmount: ?\n".format(
				latitude=latitude,
				longitude=longitude,
				datetime=dt,
			)

			with open(photo_path + ".txt", "x") as fo:
				fo.write(result)


def _smain(*, argv):
	try:
		if sys.platform == "win32":
			loop = asyncio.ProactorEventLoop()
			asyncio.set_event_loop(loop)
		else:
			loop = asyncio.get_event_loop()
		loop.run_until_complete(main(args=argv[1:], prog=argv[0], loop=loop))
	except KeyboardInterrupt:
		print(file=sys.stderr)


if __name__ == "__main__":
	sys.exit(_smain(argv=sys.argv))
