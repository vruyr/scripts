#!/workopt/python/bin/python2.7
# vim:noexpandtab:

import optparse
import os
import subprocess

def emptyDir(s):
	if os.path.isdir(s):
		if len(os.listdir(s)) > 0:
			raise ValueError("Folder exists but is not empty: " + s)
		return s
	if os.path.exists(s):
		raise ValueError("Should be folder but it is not: " + s)
	os.makedirs(s)
	return s

def main():
	parser = optparse.OptionParser()
	parser.add_option("--source", "-s", dest="srcdir", default=os.getcwd(),
		help="")
	parser.add_option("--build", "-b", dest="builddir", default=os.getcwd(),
		help="")
	parser.add_option("--install", "-i", dest="installRoot", default=os.path.expanduser("~/apps"),
		help="Path to installation root. The app will be installed as <root>/<appname>/<appversion>")
	parser.add_option("--name", "-n", dest="appname",
		help="Specify the application name that is being built (gcc, gdb, ...)")
	parser.add_option("--version", "-v", dest="appver",
		help="Specify the application version that is being built (4.6.1, 7.3.1)")
	(options, args) = parser.parse_args()

	if not options.builddir: options.builddir = options.srcdir + "-build"

	if not options.appname or not options.appver:
		nv = os.path.basename(options.srcdir).split("-")
		if len(nv) != 2: raise ValueError("Can not detect the app version, please specify manually")
		options.appname = nv[0]
		options.appver = nv[1]

	options.installdir = os.path.join(options.installRoot, options.appname, options.appver)

	emptyDir(options.installdir)
	if options.builddir != options.srcdir:
		emptyDir(options.builddir)

	print "Source  folder:", options.srcdir
	print "Build   folder:", options.builddir
	print "Install folder:", options.installdir
	print ""

	rel_configure = os.path.relpath(os.path.join(options.srcdir, "configure"), options.builddir)
	if rel_configure.find(os.path.sep) == -1:
		rel_configure = os.path.join(".", rel_configure)

	if options.builddir != os.getcwd():
		print "cd", options.builddir
	print "%s --prefix=%s" % (rel_configure, options.installdir)
	print "make -j4"
	print "make install"
	print "cd %s" % os.getcwd()
	#TODO Detect or get from options the build type (what commands to execute)


if __name__ == "__main__":
	main()
