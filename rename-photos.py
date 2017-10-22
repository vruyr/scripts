#!/usr/bin/env python3

"""
Usage:
  rename-photos.py PATH...

Description:
  Renames files passed in arguments by prepending timestamp of when the photo was originally taken.

Dependencies:
  Python Packages : docopt, pytz, tzwhere
  Commands in PATH: exiftool
"""

# Python Standard Library
import sys, argparse, subprocess, json, collections, re, datetime, decimal, os, pathlib, shlex
import threading, itertools, time
# https://pypi.python.org/pypi/docopt
import docopt
# https://pypi.python.org/pypi/pytz
import pytz
# https://pypi.python.org/pypi/tzwhere
import tzwhere.tzwhere


def main(args):
	params = docopt.docopt(__doc__, argv=args, help=True, version=True, options_first=False)
	files = params.pop("PATH")
	assert len(params) == 0, params

	photos = {}

	for photo in files:
		photos[photo] = PhotoInfo(photo)

	p = subprocess.run(
		["exiftool", "-quiet", "-short", "--printConv", "-groupNames", "-json", *files],
		input="",
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		shell=False,
		check=True,
		encoding="UTF-8",
	)
	assert not p.stderr, p.stderr

	for data in json.loads(p.stdout):
		filename = data["SourceFile"]
		ph = photos[filename]
		assert ph.path == filename, (ph.path, filename)
		ph.gpsposition = GpsPosition(
			data.get("Composite:GPSLatitude"),
			data.get("Composite:GPSLongitude")
		)
		ph.creation_date_raw = (
			# TODO This way of choosing timestamp source fallback is not elegant.
			parse_gps_date_time(data.get("EXIF:GPSDateStamp"), data.get("EXIF:GPSTimeStamp")) or
			parse_date_time(data.get("EXIF:DateTimeOriginal")) or
			parse_date_time(data.get("XMP:DateCreated")) or
			None
		)

	for name, ph in photos.items():
		assert name == ph.path
		dt = ph.creation_date
		if dt is None:
			continue
		path = pathlib.Path(ph.path)
		newpath = path.parent / "{:%Y%m%dT%H%M%S%z} {}".format(dt, path.name)
		assert not newpath.exists()
		path.rename(newpath)

		print(shlex.quote(str(path)), "->", shlex.quote(str(newpath)))


def parse_gps_date_time(gps_date_stamp, gps_time_stamp):
	if gps_date_stamp is None and gps_time_stamp is None:
		return None
	return parse_date_time("{} {}".format(gps_date_stamp, gps_time_stamp), datetime.timezone.utc)


def parse_date_time(dt, tzinfo=None):
	if dt is None:
		return None
	m = re.match(r"^(\d{4}):(\d{2}):(\d{2}) (\d{2}):(\d{2}):(\d{2})(\.\d+)?$", dt)
	assert m, dt
	year, month, day, hour, minute, second, subseconds = m.groups()
	d = datetime.datetime(
		year=int(year),
		month=int(month),
		day=int(day),
		hour=int(hour),
		minute=int(minute),
		second=int(second),
		microsecond=int(decimal.Decimal("0" + subseconds) * 1000000) if subseconds is not None else 0,
		tzinfo=tzinfo,
	)
	return (dt, d)


class PhotoInfo(object):
	def __init__(self, path):
		self._path = path
		self._creation_date_raw = None
		self._gpsposition = None
		self._timezone_name = None

	def __repr__(self):
		return "PhotoInfo(path={!r}, gpsposition={!r}, creation_date_str={!r}, timezone_name={!r})".format(
			self.path,
			self.gpsposition,
			self.creation_date_str,
			self.timezone_name,
		)

	@property
	def path(self):
		return self._path

	@property
	def creation_date_raw(self):
		return self._creation_date_raw

	@creation_date_raw.setter
	def creation_date_raw(self, value):
		assert isinstance(value, tuple) and isinstance(value[0], str) and isinstance(value[1], datetime.datetime)
		self._creation_date_raw = value

	@property
	def creation_date_str(self):
		if self.creation_date_raw is None:
			return None
		return self.creation_date_raw[0]

	@property
	def creation_date_dt(self):
		if self.creation_date_raw is None:
			return None
		return self.creation_date_raw[1]

	@property
	def creation_date(self):
		dt = self.creation_date_dt
		if dt is None:
			return None
		if dt.tzinfo is not None and self.timezone is not None:
			return dt.astimezone(self.timezone)
		else:
			return dt

	@property
	def timezone_name(self):
		if self._timezone_name is None and self.gpsposition and self.gpsposition.latitude and self.gpsposition.longitude:
			self._timezone_name = self.tzwhere.tzNameAt(self.gpsposition.latitude, self.gpsposition.longitude)
		return self._timezone_name

	@property
	def gpsposition(self):
		return self._gpsposition

	@gpsposition.setter
	def gpsposition(self, value):
		self._gpsposition = value
		if self._gpsposition is not None and self._gpsposition.latitude is None and self._gpsposition.longitude is None:
			self._gpsposition = None
		return self.gpsposition

	@property
	def timezone(self):
		if self.timezone_name is not None:
			return pytz.timezone(self.timezone_name)
		return None

	_tzwhere = None

	@property
	def tzwhere(self):
		if self.__class__._tzwhere is None:
			with Spinner("Loading gps position to timezone mapping"):
				self.__class__._tzwhere = tzwhere.tzwhere.tzwhere()
		return self.__class__._tzwhere


class GpsPosition(object):
	def __init__(self, latitude, longitude):
		self.latitude = latitude
		self.longitude = longitude

	def __repr__(self):
		return "GpsPosition({:.6f}, {:.6f})".format(self.latitude, self.longitude)


class Spinner(object):
	def __init__(self, msg="", *, stream=sys.stderr, frames=0, interval=0.075, sep=" ", end="\n"):
		self._stream = stream
		assert self._stream.isatty()
		self._message = msg
		assert isinstance(self._message, str)
		self._frames = frames
		if isinstance(self._frames, int):
			self._frames = self.FRAMES_OPTIONS[self._frames]
		self._interval = interval
		assert isinstance(self._interval, (float, int, decimal.Decimal))
		self._sep = sep
		assert isinstance(self._sep, str)
		self._end = end
		assert isinstance(self._end, str)
		self._stop = False
		self._thread = None

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.stop()

	def start(self):
		self._stream.write(self._message)
		self._stream.flush()
		self._set_frame()
		self._stop = False
		self._thread = threading.Thread(target=self._run)
		self._thread.start()

	def stop(self):
		self._stop = True
		self._thread.join()
		self._thread = None
		self._reset_frame()
		self._stream.write(self._end)
		self._stream.flush()

	def _run(self):
		for frame in itertools.cycle(self._frames):
			if self._stop:
				break
			self._reset_frame()
			self._stream.write(self._sep)
			self._stream.write(frame)
			self._stream.flush()
			time.sleep(self._interval)

	def _set_frame(self):
		self._stream.write("\x1b7") # https://stackoverflow.com/a/29163244/2084761
		self._stream.flush()

	def _reset_frame(self, *, flush=False):
		self._stream.write("\x1b8") # https://stackoverflow.com/a/29163244/2084761
		self._stream.write("\x1b[0K")
		if flush:
			self._stream.flush()

	FRAMES_OPTIONS = [
		[
			"[          ]",
			"[>         ]",
			"[~>        ]",
			"[~~>       ]",
			"[ ~~>      ]",
			"[  ~~>     ]",
			"[   ~~>    ]",
			"[    ~~>   ]",
			"[     ~~>  ]",
			"[      ~~> ]",
			"[       ~~>]",
			"[        ~~]",
			"[         ~]",
			"[          ]",
			"[          ]",
			"[         <]",
			"[        <~]",
			"[       <~~]",
			"[      <~~ ]",
			"[     <~~  ]",
			"[    <~~   ]",
			"[   <~~    ]",
			"[  <~~     ]",
			"[ <~~      ]",
			"[<~~       ]",
			"[~~        ]",
			"[~         ]",
			"[          ]",
		],
	]


if __name__ == "__main__":
	try:
		sys.exit(main(sys.argv[1:]))
	except KeyboardInterrupt:
		sys.stderr.write("\n")
