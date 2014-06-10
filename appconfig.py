#!/usr/bin/env python2.7
# vim:noexpandtab:

VERSION="0.1.0"

"""
This script is for spitting environment variables to make software available system-wide.
"""

import os, platform, optparse, sys, re

colors = {
	"reset":   "\x1b[m",
	"red":     "\x1b[31m",
	"green":   "\x1b[32m",
	"yellow":  "\x1b[33m",
	"blue":    "\x1b[34m",
	"magenta": "\x1b[35m",
	"cyan":    "\x1b[36m",
	"white":   "\x1b[37m",
}
def log(*args, **kw):
	if kw.get("color", None) and sys.stderr.isatty():
		sys.stderr.write(colors[kw["color"]])

	sys.stderr.write("".join(args))

	if sys.stderr.isatty():
		sys.stderr.write(colors["reset"])

	sys.stderr.write("\n")


def main():
	parser = optparse.OptionParser(
		usage="Usage: %prog [options] [app..]",
		version="%prog v" + VERSION,
		description="If invoked without arguments, tries to read the list of apps from "
			"ROOT/defaults (one app per line) else prints config for all apps. "
			"If arguments are specified -- only prints config for specified apps. "
			"Example for sh/bash to put in ~/.profile: eval `%prog --format=sh dmd gcc doxygen`. "
			"If app name argument is in form of app:version the specified version "
			"of the app will be loaded (eval `%prog -fsh gcc:4.6.0`). "
	)
	parser.add_option("-r", "--root", dest="root",  default=os.path.expanduser("~/apps"),
		help="Specify the root apps folder where the apps will be searched")
	parser.add_option("-x", "--exclude", dest="exclude", action="append",
		help="do not load configuration for APP", metavar="APP")
	parser.add_option("-f", "--format", dest="format", default="sh",
		help="spit out configuration in specified format (bash, csh, ...)", metavar="FORMAT")
	parser.add_option("-p", "--platform", dest="platform", action="store",
		help="load configurations for specified platform")
	parser.add_option("-d", "--defaults", dest="defaults", action="store_true", default=False,
		help="load all default apps")
	parser.add_option("-q", "--quiet", dest="quiet", action="store_true", default=False)
	(options, args) = parser.parse_args()

	if options.defaults:
		defaults = os.path.join(options.root, "defaults")
		if os.path.exists(defaults):
			args = map(lambda x: x.strip(), open(defaults, "r").readlines())
		else:
			args = filter(lambda x: not x.startswith("."), os.listdir(options.root))

	if not args:
		for x in filter(lambda x: not x.startswith("."), os.listdir(options.root)):
			approot = os.path.join(options.root, x)
			if not os.path.isdir(approot): continue
			log(os.path.basename(x).ljust(16), ": ", ", ".join(filter(lambda x: os.path.isdir(os.path.join(approot, x)), os.listdir(approot))))
		return

	nonPathVars = {}

	pathVars = {
		"PATH": [],
		"LD_LIBRARY_PATH": [],
		"LD_RUN_PATH": [],
		"MANPATH": [],
		"PYTHONPATH": [],
		"CPATH": [],
		"PKG_CONFIG_PATH": [],
	}

	def appendPath(var, appname, appver, *dirs):
		verdir = os.path.join(options.root, appname, appver)
		if os.path.islink(verdir):
			verdir = os.readlink(verdir)
		p = os.path.join(verdir, *dirs)
		if os.path.isdir(p):
			pathVars.setdefault(var, list()).append(p)

	def setVar(var, val):
		val = os.path.join(options.root, val)
		nonPathVars[var] = val

	def printForBash():
		forExport = list()
		for var, value in nonPathVars.items():
			print "%(var)s=%(value)s" % { "var": var, "value": value }
			forExport.append(var)

		for var, values in pathVars.items():
			if not values: continue
			suffix = ""
			if var == "MANPATH":
				suffix = ":"
			print "%(var)s=%(values)s${%(var)s:+:${%(var)s}}%(suffix)s" % { "var": var, "values": ":".join(values), "suffix": suffix }
			forExport.append(var)
		if len(forExport) > 0:
			print "export " + " ".join(forExport)

	def printForCsh():
#		print "setenv TEMP_SOURCE_FILE `mktemp`"
		for var, value in nonPathVars.items():
			print "setenv %(var)s %(value)s;" % { "var": var, "value": value }

		for var, values in pathVars.items():
			if not values: continue
			suffix = ""
			if var == "MANPATH":
				suffix = ":"
			print "set sfx=''"
			print "if ( $?%(var)s ) then\n\tif ( $%(var)s != '' ) set sfx=:$%(var)s\nendif" % { "var": var }
			print "setenv %(var)s %(values)s${sfx}%(suffix)s;" % {  #echo >${TEMP_SOURCE_FILE}
				"var": var,
				"values": ":".join(values),
				"suffix": suffix
			}
#		print "source ${TEMP_SOURCE_FILE}"
#		print "rm ${TEMP_SOURCE_FILE}"

	osName = platform.uname()[0].lower()
	osArch = platform.uname()[4].lower()
	#TODO load only software that can actually run on this machine

	loaded = []
	for app in args:
		app_ = app.split(":", 1)
		if len(app_) == 1:
			app_.append(None)
		appname, appvers = app_

		approot = os.path.join(options.root, appname)
		if not os.path.isdir(approot):
			log("No such app '", appname, "'. Ignoring.", color="red")
			continue
		if not appvers:
			appvers = os.path.join(sorted(filter(lambda x: os.path.isdir(os.path.join(approot, x)), os.listdir(approot)))[-1])
		elif not os.path.isdir(os.path.join(approot, appvers)):
			log("No such version '", appvers, "' for app '", appname, "'. Ignoring.", color="red")
			continue

		loaded.append(appname+":"+appvers)

		config = os.path.join(options.root, appname, "config")
		if os.path.isfile(config):
			r = re.compile(r"^\s*(\w+)\s+([^\s#]+).*$")
			comment = re.compile(r"^\s*(#.*)?$")
			for l in open(config).readlines():
				if comment.match(l):
					continue
				m = r.match(l)
				if not m:
					log("Invalid config line: ", l)
					continue
				var, val = m.group(1, 2)
				if var in pathVars:
					appendPath(var, appname, appvers, val)
				else:
					setVar(var, os.path.join(appname, appvers, val))
		else:
			appendPath("PATH",            appname, appvers, "bin")
			appendPath("PATH",            appname, appvers, "sbin")
			appendPath("LD_LIBRARY_PATH", appname, appvers, "lib")
			appendPath("LD_RUN_PATH",     appname, appvers, "lib")
			appendPath("LIBRARY_PATH",    appname, appvers, "lib")
			appendPath("CPATH",           appname, appvers, "include")
			appendPath("MANPATH",         appname, appvers, "man")
			appendPath("MANPATH",         appname, appvers, "share", "man")
			appendPath("PKG_CONFIG_PATH", appname, appvers, "lib", "pkgconfig")

	formatters = {
		"sh"  : printForBash,
		"bash": printForBash,
		"csh" : printForCsh,
		"tcsh": printForCsh
	}
	formatters[options.format]()

	if loaded and not options.quiet:
		log("Loaded apps by appconfig: " + ", ".join(['\x1b[35m' + x + '\x1b[m' for x in loaded]), color="magenta")



if __name__ == "__main__":
	main()
