#!/usr/bin/env python3

import subprocess, datetime, os, pathlib

volumes = ["/", pathlib.Path.home()]
packages = []
for volume in volumes:
	p = subprocess.run(["pkgutil", "--volume", volume, "--pkgs"], stdout=subprocess.PIPE)
	if p.returncode:
		continue
	for pkg_id in p.stdout.splitlines():
		pinfo = {}
		for f in subprocess.check_output(["pkgutil", "--volume", volume, "--pkg-info", pkg_id], encoding="UTF-8").splitlines():
			key, value = f.split(": ")
			pinfo[key] = value
		pinfo["install-time"] = datetime.datetime.fromtimestamp(int(pinfo["install-time"]))
		packages.append(pinfo)

for p in sorted(packages, key=lambda p: p["install-time"]):
	print("{install-time} {package-id:60} {version:30} {volume:13} {location}".format(**p))
