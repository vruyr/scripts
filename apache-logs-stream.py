#!/usr/bin/env python3

"""
Usage:
	{prog} [options] --server-host=ADDRESS --log-file-path=PATH [--exclude-host=ADDRESS]...

Options:
	--oneline                           Stream logs in a compact format.
	--since=DATE, -s DATE               Only show logs after specified date and time.
	--exclude-host=ADDRESS, -x ADDRESS  Do not show logs initiated from specified IP addresses.
	--server-host=ADDRESS, -h ADDRESS   The server hostname to get apache logs from.
	--log-file-path=PATH, -p PATH       Path to the access log file on the specified remote host.
"""

import sys, locale, asyncio, subprocess, os, socket, datetime, re, json
# pip install docopt==0.6.2
import docopt
# pip install geoip2==4.0.2
import geoip2.database
# pip install dateparser==0.7.6
import dateparser


async def main(*, args, prog):
	locale.setlocale(locale.LC_ALL, "")

	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	server_host = params.pop("--server-host")
	log_file_path = params.pop("--log-file-path")
	stream_oneline = params.pop("--oneline")
	since_time = params.pop("--since")
	exclude_hosts_addresses = params.pop("--exclude-host")
	if since_time:
		since_time = dateparser.parse(since_time, settings={"RETURN_AS_TIMEZONE_AWARE": True})
	assert not params, params

	log = asyncio.Queue()
	pending_tasks = []
	printer_task = asyncio.create_task(
		printer(queue=log, fo=sys.stdout)
	)

	#{

	exclude_hosts = []
	for a in exclude_hosts_addresses:
		exclude_hosts.extend(socket.gethostbyname_ex(a)[2])

	cmd = [
		"ssh", server_host,
		"tail", "--follow=name", "--lines=+0",
		log_file_path,
	]
	p = await asyncio.create_subprocess_exec(
		*cmd,
		stdout=subprocess.PIPE,
	)
	pending_tasks.append(p.wait()) #TODO call p.terminate() at exit
	pending_tasks.append(process_apache_access_log(
		input_stream=p.stdout,
		output_queue=log,
		exclude_hosts=exclude_hosts,
		oneline=stream_oneline,
		since=since_time,
	))

	#}

	await asyncio.gather(*pending_tasks)
	current_task = asyncio.current_task()
	all_tasks = asyncio.all_tasks()
	assert {current_task, printer_task} == all_tasks, (current_task, all_tasks)

	await log.put(None)
	await printer_task


async def process_apache_access_log(*, input_stream, output_queue, exclude_hosts=None, oneline=False, since=None):
	# LogFormat "%h %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\"" combined
	# http://httpd.apache.org/docs/current/mod/mod_log_config.html

	line_p = re.compile(r"""^(?P<remote_hostname>\S+) (?P<remote_logname>\S+) (?P<remote_user>\S+) \[(?P<time>[^]]+)\] "(?P<request_first_line>[^"]+)" (?P<final_status>\S+) (?P<bytes_sent>\d+) "(?P<referrer>[^"]+)" "(?P<useragent>[^"]+)"\s*$""")
	request_p = re.compile(r"""^(?P<method>\S+)\s+(?P<uri>.*)\s+(?P<httpversion>\S+)\s*$""")

	def json_default(o):
		if isinstance(o, datetime.datetime):
			return o.isoformat()
		raise TypeError(f"Object of type {o.__class__.__name__!r} is not JSON serializable")

	# https://github.com/maxmind/GeoIP2-python
	# https://dev.maxmind.com/#GeoIP
	with geoip2.database.Reader("/Users/vruyr/.bin/geoip2/GeoLite2-City_20200804/GeoLite2-City.mmdb") as geoip_reader_city:
		with geoip2.database.Reader("/Users/vruyr/.bin/geoip2/GeoLite2-ASN_20200811/GeoLite2-ASN.mmdb") as geoip_reader_asn:
			while True:
				line = await input_stream.readline()
				if not line:
					break
				line = line.decode("UTF-8") #TODO Don't assume UTF-8 encoding.
				linedict = line_p.match(line).groupdict()
				linedict["time"] = datetime.datetime.strptime(linedict["time"], "%d/%b/%Y:%H:%M:%S %z")
				if since and linedict["time"] < since:
					continue
				if m := request_p.match(linedict["request_first_line"]):
					linedict["request"] = m.groupdict()
				else:
					linedict["request"] = None
				remote_hostname = linedict["remote_hostname"]
				if exclude_hosts and remote_hostname in exclude_hosts:
					continue
				geoip_city = None
				geoip_asn = None
				try:
					geoip_city = geoip_reader_city.city(remote_hostname)
				except:
					pass
				try:
					geoip_asn = geoip_reader_asn.asn(remote_hostname)
				except:
					pass
				linedict["geoip"] = format_geoip(geoip_city, geoip_asn)

				if oneline:
					f_time = linedict["time"].isoformat()
					f_method = (linedict.get("request") or {}).get("method", "<none>")
					f_status = linedict["final_status"]
					f_remote_host = linedict["remote_hostname"]
					f_city = linedict["geoip"]["city"] or "-"
					f_country = linedict["geoip"]["country"]["iso_code"] or "-"
					f_uri = (linedict.get("request") or {}).get("uri", repr(linedict["request_first_line"]))
					await output_queue.put(f"""{f_time} {f_method:8} {f_status} {f_remote_host:15} {f_city:20} {f_country:2} {f_uri}\n""")
				else:
					await output_queue.put(json.dumps(linedict, indent="\t", default=json_default))
					await output_queue.put("\n")


def format_geoip(geoip_city, geoip_asn):
	return {
		"autonomous_system_organization": geoip_asn.autonomous_system_organization if geoip_asn else None,
		"city": geoip_city.city.name if geoip_city else None,
		"subdivisions": [s.name for s in geoip_city.subdivisions] if geoip_city else [],
		"postal": geoip_city.postal.code if geoip_city else None,
		"country": {
			"name": geoip_city.country.name if geoip_city else None,
			"iso_code": geoip_city.country.iso_code if geoip_city else None,
		},
		"continent": geoip_city.continent.name if geoip_city else None,
		"location": {
			"latitude": geoip_city.location.latitude if geoip_city else None,
			"longitude": geoip_city.location.longitude if geoip_city else None,
			"accuracy_radius": geoip_city.location.accuracy_radius if geoip_city else None,
		}
	}


async def printer(*, queue, fo):
	while True:
		item = await queue.get()
		if item is None:
			break
		if isinstance(item, (list, tuple)):
			print(*item, file=fo, sep="", end="")
		else:
			print(item, file=fo, sep="", end="")


def smain(argv=None):
	if argv is None:
		argv = sys.argv

	try:
		if sys.platform == "win32":
			asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

		return asyncio.run(
			main(
				args=argv[1:],
				prog=argv[0]
			),
			debug=False,
		)
	except KeyboardInterrupt:
		print(file=sys.stderr)


if __name__ == "__main__":
	sys.exit(smain())
