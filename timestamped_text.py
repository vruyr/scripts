#!/usr/bin/env python3

import sys, re, datetime

time_p = re.compile("(?:(\d+)(?::(\d+))?\s*(am|pm))", re.I)

def parse_ampm_time_prefix(s):
	m = time_p.match(s)
	if m is None:
		return None
	hour, minute, ampm = m.groups()
	if minute is None:
		minute = 0
	hour = int(hour)
	minute = int(minute)
	if (hour, ampm) == (12, "am"):
		hour = 0
	elif ampm == "pm" and hour != 12:
		hour += 12
	return datetime.datetime.now().replace(
		hour=hour,
		minute=minute,
		second=0,
		microsecond=0
	)

def parse_lines(lines):
	for line in lines:
		the_time = parse_ampm_time_prefix(line)
		yield (the_time, line)
	yield (datetime.datetime.now().replace(microsecond=0), "(now)")

def format_timedelta(td):
	seconds = int(td.total_seconds())
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)
	result = []
	if hours:
		result.append(f"{hours}h")
	if minutes:
		result.append(f"{minutes:>2}m")
	if seconds:
		result.append(f"{seconds:>2}s")
	return " ".join(result)

# with open(sys.argv[1], "r", encoding="UTF-8") as fo:
fo = sys.stdin
the_time_prev = None
for the_time, line in parse_lines(fo.readlines()):
	line = line.rstrip()
	prefix = ""
	if the_time is not None and the_time_prev is not None:
		prefix = format_timedelta(the_time - the_time_prev)
	print("[", prefix.rjust(7), "] ", line, sep="")
	if the_time is not None:
		the_time_prev = the_time
