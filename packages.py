#!/usr/bin/env python

import subprocess, datetime, os

packages = []
for p in subprocess.check_output(["pkgutil", "--pkgs"]).splitlines():
	pinfo = {}
	for f in subprocess.check_output(["pkgutil", "--pkg-info", p]).splitlines():
		key, value = f.split(": ")
		pinfo[key] = value
	pinfo["install-time"] = datetime.datetime.fromtimestamp(int(pinfo["install-time"]))
	packages.append((
		pinfo["install-time"],
		pinfo["package-id"],
		pinfo["version"],
		pinfo["volume"],
		pinfo["location"]
	))
packages = sorted(packages)

for p in packages:
	p = map(str, p)
	print p[0].ljust(20), p[1].ljust(60), p[2].ljust(30), os.path.join(p[3], p[4]).ljust(10)
