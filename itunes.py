#!/usr/bin/env python3

"""
Usage:
	{prog} [--name=IOS_DEVICE_NAME]... [--exclude=IOS_DEVICE_NAME]... <command>

Options:
	--name, -n IOS_DEVICE_NAME     Only operate on specified devices.
	--exclude, -x IOS_DEVICE_NAME  Names of iOS Devices to exclude.
"""

import sys, os, json, subprocess
# pip install 'docopt>=0.6.2'
import docopt
# pip install 'pyobjc-framework-ScriptingBridge>=5.1.2'
import ScriptingBridge
# pip install 'pyobjc-framework-Cocoa>=5.1.2'
import Foundation


def main(*, args, prog):
	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	names = params.pop("--name")
	excluded_names = params.pop("--exclude")
	command = params.pop("<command>")
	assert not params, params

	app = ScriptingBridge.SBApplication.applicationWithBundleIdentifier_("com.apple.iTunes")

	devices = app.sources().filteredArrayUsingPredicate_(
		Foundation.NSPredicate.predicateWithFormat_("kind == 'kPod'")
	)
	for source in devices:
		assert objcEnumToStr(source.kind()) == b"kPod"
		name = source.name()
		if names and name not in names or name in excluded_names:
			continue
		do_command(command, source)
		print(name)


def do_command(command, device):
	if command == "sync":
		device.update()
	else:
		raise ValueError(f"unrecognized command {command!r}")


def show_ios_backups():
	p = subprocess.run(
		["cfgutil", "--format", "json", "list-backups"],
		capture_output=True,
		check=True,
		encoding="UTF-8"
	)
	assert not p.stderr, p.stderr
	data = json.loads(p.stdout)
	popAssert(data, "Command", "list-backups")
	popAssert(data, "Type", "CommandOutput")
	output = data.pop("Output")
	for backup in output:
		print(f"""{backup["Date"]} {backup["Name"]}""")


def popAssert(o, k, v):
	assert o[k] == v, (k, v, o)
	del o[k]


def objcEnumToStr(int_value):
	return int_value.to_bytes(length=4, byteorder="big")


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
