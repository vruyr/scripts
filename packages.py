#!/usr/bin/env python3

import subprocess, datetime, os, sys, pathlib, plistlib, json

try:
	pkg_ids = sys.argv[1:]

	if not pkg_ids:
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

		sys.exit(0)


	for pkg_id in pkg_ids:
		p = subprocess.run(["pkgutil", "--export-plist", pkg_id], stdout=subprocess.PIPE, encoding=None)
		if p.returncode:
			continue
		metadata = plistlib.loads(p.stdout)
		assert metadata.pop("pkgid") == pkg_id
		install_root = os.path.join(metadata.pop("volume"), metadata.pop("install-location"))
		install_time = datetime.datetime.fromtimestamp(metadata.pop("install-time"))
		installed_files = [os.path.join(install_root, i) for i in metadata.pop("paths").keys()]
		print(install_time, pkg_id)
		installed_files_missing = []
		installed_files_present = []

		for i in installed_files:
			if os.path.exists(i):
				installed_files_present.append(i)
			else:
				installed_files_missing.append(i)

		print("Missing files:", json.dumps(installed_files_missing, indent="    "))
		print("Present files:", json.dumps(installed_files_present, indent="    "))

		user_input = input("\nTo delete present files and forget the package receipt type \"delete\": ")
		if user_input != "delete":
			print("Doing nothing!")
			sys.exit(0)
		for i in reversed(installed_files):
			if not os.path.exists(i):
				continue
			print("Unlinking", json.dumps(i))
			os.unlink(i)
		print("Forgetting package receipt for", json.dumps(pkg_id))
		p = subprocess.run(["pkgutil", "--forget", pkg_id])
		if p.returncode:
			print("FAILED:", p.returncode)
except KeyboardInterrupt:
	print()
