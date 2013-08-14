#!/usr/bin/env rdmd

import std.stdio, std.format, std.datetime, std.conv, std.string, std.regex;

void main(string args[])
{
	string input = args[1];
	double d;
	string units, msg;
	string time;

	auto now = Clock.currTime();

	auto timePattern = regex(`^\s*=\s*(?P<hours>\d{1,2}):(?P<minutes>\d{1,2})(?::(?P<seconds>\d{1,2}))?\s*(?P<ampm>am|pm)?\s*(?P<comment>.*)$`, "i");
	auto shiftPattern = regex(`^\s*-\s*((?P<hours>\d+)h)?\s*((?P<minutes>\d+)m)?\s*((?P<seconds>\d+)s\b)?\s*(?P<comment>.*)$`, "i");

	if(auto m = match(input, timePattern))
	{
		auto c = m.captures;

		int hours = (c["hours"].length)?(to!int(c["hours"])):0;
		int minutes = (c["minutes"].length)?(to!int(c["minutes"])):0;
		int seconds = c["seconds"].length?(to!int(c["seconds"])):0;
		if(toLower(c["ampm"]) == "pm")
			hours += 12;

		writeln(SysTime(DateTime(now.year, now.month, now.day, hours, minutes, seconds)), " ", c["comment"]);
	}
	else if(auto m = match(input, shiftPattern))
	{
		auto c = m.captures;
		auto hours = c["hours"].length ? to!double(c["hours"]) : 0.0;
		auto minutes = c["minutes"].length ? to!double(c["minutes"]) : 0.0;
		auto seconds = c["seconds"].length ? to!double(c["seconds"]) : 0.0;

		auto duration = cast(Duration)(
			cast(TickDuration)(dur!"hours"(1)) * hours +
			cast(TickDuration)(dur!"minutes"(1)) * minutes + 
			cast(TickDuration)(dur!"seconds"(1)) * seconds
		);
		
		writeln(Clock.currTime - duration);
		writeln(duration, " | ", c["comment"]);
	}
}
