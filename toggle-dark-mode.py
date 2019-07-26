#!/usr/bin/env python3

"""
Usage:
	{prog}
"""

import sys, locale, os
# pip install docopt==0.6.2
import docopt
# pip install 'pyobjc-framework-ScriptingBridge>=5.1.2'
import ScriptingBridge


def main(*, args, prog):
	locale.setlocale(locale.LC_ALL, "")

	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	assert not params, params

	app = ScriptingBridge.SBApplication.applicationWithBundleIdentifier_("com.apple.systemevents")
	prefs = app.appearancePreferences()
	prefs.setDarkMode_(not prefs.darkMode())


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
