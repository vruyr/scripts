#!/usr/bin/env python3

"""
Description
"""

import sys, locale, argparse, asyncio, os
import pyatv, pyatv.const, pyatv.storage.file_storage


# https://github.com/postlund/pyatv/issues/2512
# https://github.com/postlund/pyatv/issues/2403


async def main(
	*,
	# Example Options
	example,
	# Target Device Selection
	hosts,
):
	locale.setlocale(locale.LC_ALL, "")

	loop = asyncio.get_running_loop()

	#
	# https://pyatv.dev/development/
	#

	storage_path = os.path.expanduser("~/.config/airplay.py.json")
	storage = pyatv.storage.file_storage.FileStorage(storage_path, loop)
	await storage.load()

	atv_conf = await pyatv.scan(loop, hosts=hosts, protocol={pyatv.const.Protocol.AirPlay}, storage=storage)

	assert len(atv_conf) == 1, ("Expected exactly one Apple TV device to be found", atv_conf)
	atv_conf = atv_conf[0]
	print(atv_conf.name, atv_conf.address, atv_conf.device_info)

	await pair_with_appletv_protocol(atv_conf, loop, storage, pyatv.const.Protocol.AirPlay)

	atv = await pyatv.connect(atv_conf, loop, storage=storage)

	await atv.stream.play_url("http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4")

	await asyncio.gather(*atv.close())

	#
	# END
	#

	await storage.save()


async def pair_with_appletv_protocol(atv_conf, loop, storage, protocol):
	# https://pyatv.dev/development/scan_pair_and_connect/

	atv_service = atv_conf.get_service(protocol)
	if not atv_service:
		print(f"Service {protocol} not found in {atv_conf.name}")
		return

	# Do we need to pair?
	if atv_service.pairing not in (
		pyatv.const.PairingRequirement.Optional,
		pyatv.const.PairingRequirement.Mandatory,
	):
		return

	# Are we already paired?
	if atv_service.credentials:
		return

	pairing = await pyatv.pair(atv_conf, protocol, loop, storage=storage)
	try:
		await pairing.begin()

		if pairing.device_provides_pin:
			pin = int(input("Enter PIN: "))
			pairing.pin(pin)
		else:
			pairing.pin(1234)  # Should be randomized
			input("Enter this PIN on the device: 1234")

		await pairing.finish()

		if not pairing.has_paired:
			raise RuntimeError("Did not pair with device!")

		assert pairing.service.credentials

		await storage.save()
	finally:
		await pairing.close()



def parse_args(*, args, prog):
	parser = argparse.ArgumentParser(
		prog=prog,
		usage="%(prog)s [OPTIONS]...",
		description=__doc__,
		formatter_class=argparse.RawTextHelpFormatter,
		fromfile_prefix_chars="@",
		add_help=False,
	)

	the_default = "\ndefault: %(default)s"

	options_generic = parser.add_argument_group("Generic Options")
	options_generic.add_argument(
		"--help", "-h",
		action="help",
		help="show help message and exit",
	)

	options_example = parser.add_argument_group("Example Options")
	options_example.add_argument(
		"--example", "-e", metavar="NUMBER",
		action="store", dest="example", type=int, default=None, required=False,
		help="an example option that accepts an integer" + the_default
	)

	options_network = parser.add_argument_group("Target Device Selection")
	options_network.add_argument(
		"--host", "-H", metavar="ADDRESS",
		action="append", dest="hosts", default=None, required=False,
		help="Apple TV host IP or name; may be specified multiple times" + the_default
	)

	opts = parser.parse_args(args)
	return vars(opts)


def configure_logging(opts):
	pass


def smain(argv=None):
	if argv is None:
		argv = sys.argv

	try:
		opts = parse_args(args=argv[1:], prog=argv[0])
		configure_logging(opts)

		if sys.platform == "win32":
			asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

		return asyncio.run(
			main(**opts),
			debug=False,
		)
	except KeyboardInterrupt:
		print(file=sys.stderr)


if __name__ == "__main__":
	sys.exit(smain())
