#!/usr/bin/env python3

"""
Usage:
	{prog}

Options:
	--version   Print the version number and exit.
	--help, -h  Show this help screen and exit.
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
	assert not params, params

	#TODO Find out a way to get the app by path.


	#TODO Filtering in python is slow - find a way to have the array filter itself. The pp.filteredArrayUsingPredicate_(Foundation.NSPredicate.predicateWithFormat_("applicationFile.POSIXPath == '/Applications/Safari.app'")) exits with error message "only simple keys, not key paths, are currently supported". How does AppleScript do the `get every item of application processes where POSIX path of application file is "/Applications/Safari.app"`

	systemevents = ScriptingBridge.SBApplication.applicationWithBundleIdentifier_("com.apple.systemevents")
	safariProcess = findOne(systemevents.applicationProcesses(), lambda p: p.applicationFile().POSIXPath() == "/Applications/Safari.app")
	menu_bar = findOne(safariProcess.UIElements(), lambda e: e.role() == "AXMenuBar")
	menu_safari = findOne(menu_bar.UIElements(), lambda e: e.role() == "AXMenuBarItem" and e.name() == "Safari")
	menu_safari = findOne(menu_safari.UIElements(), lambda e: e.role() == "AXMenu")
	menu_preferences = findOne(menu_safari.UIElements(), lambda e: e.role() == "AXMenuItem" and e.name() == "Preferences\u2026")
	menu_preferences.clickAt_(menu_preferences)


def findOne(l, pred):
	return getSingleItem(filter(pred, l))


def getSingleItem(l):
	item = None
	for i in l:
		if item is not None:
			assert False, l
		item = i
	return item


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
