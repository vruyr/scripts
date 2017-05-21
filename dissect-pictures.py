#!/usr/bin/env python3

import sys, argparse, os, subprocess, json, urllib.parse


def main(opts):
	print("The script doesn't work as expected because of bogus metadata in some of the photos. Refactoring is needed.")
	return

	source = os.path.expanduser(os.path.join("~", "Pictures", "__INBOX__"))
	target = os.path.expanduser(os.path.join("~", "Pictures", "__INBOX_WITH_METADATA__"))
	common = 4
	if True:
		json_text = subprocess.check_output([
			"exiftool",
			"-b", "-j",
			"-EXIF:Make",
			"-EXIF:Model",
			"-EXIF:CreateDate",
			"-GPSDateTime",
			"-GPSCoordinates",
			"-r", source
		]).decode()
		with open("__INBOX__.json", "w") as f:
			f.write(json_text)
	else:
		with open("__INBOX__.json", "r") as f:
			json_text = f.read()

	data = json.loads(json_text)

	makemodel_trusted = (
		('Apple', 'iPad 2'),
		('Apple', 'iPad mini'),
		('Apple', 'iPad'),
		('Apple', 'iPhone 4'),
		('Apple', 'iPhone 4S'),
		('Apple', 'iPhone 5'),
		('Apple', 'iPhone 5s'),
		('Canon', 'Canon EOS 5D Mark II'),
		('Canon', 'Canon EOS 60D'),
		('Canon', 'Canon EOS 650D'),
		('Canon', 'Canon EOS REBEL T4i'),
		('Canon', 'Canon EOS-1Ds Mark III'),
		('Canon', 'Canon PowerShot A620'),
		('Canon', 'Canon PowerShot A800'),
		('Canon', 'Canon PowerShot S5 IS'),
		('Canon', 'Canon PowerShot S95'),
		('Canon', 'Canon PowerShot SD850 IS'),
		('Canon', 'Canon PowerShot SX20 IS'),
		('CASIO COMPUTER CO.,LTD.', 'EX-Z850'),
		('HTC', 'ADR6300'),
		('HTC', 'HTC Touch Diamond P3700'),
		('HTC', 'T-Mobile G1'),
		('Motorola', 'DROIDX 26400001ffd800000a3a9a5d0e02a013'),
		('NIKON CORPORATION', 'NIKON D7000'),
		('NIKON', 'COOLPIX L24'),
		('NIKON', 'COOLPIX S3000'),
		('NIKON', 'E3100'),
		('NIKON', 'E4300'),
		('SONY', 'DSC-T30'),
		('SONY', 'DSC-T700'),
		('OLYMPUS IMAGING CORP.', 'E-420'),
		('OLYMPUS OPTICAL CO.,LTD', 'C990Z,D490Z'),
		('PENTAX Corporation', 'PENTAX *ist D'),
	)
	makemodel_unknown = set()
	root_parts = source.split(os.path.sep)
	for rec in data:
		if "GPSCoordinates" not in rec and ("Make" not in rec or "Model" not in rec or "CreateDate" not in rec):
			continue
		source_path = rec["SourceFile"]
		source_path_parts = source_path.split(os.path.sep)
		if source_path_parts[:len(root_parts)] != root_parts:
			continue

		rec.setdefault("Make", "Unknown Make")
		rec.setdefault("Model", "Unknown Model")
		makemodel = (rec["Make"], rec["Model"])
		if "GPSCoordinates" not in rec and makemodel not in makemodel_trusted:
			makemodel_unknown.add(makemodel)
			continue

		makemodel_dirname = urllib.parse.quote("{Model} ({Make})".format(**rec), safe=" ()")
		if "GPSDateTime" in rec:
			makemodel_dirname = os.path.join("GPSDateTime", makemodel_dirname)
		relpath_parts = source_path_parts[len(root_parts):]
		newpath_parts = [makemodel_dirname] + relpath_parts
		target_path = os.path.join(target, os.path.sep.join(newpath_parts))
		os.makedirs(os.path.dirname(target_path), exist_ok=True)
		if os.path.exists(target_path):
			print("WARNING: already exist, doing nothing - %s" % target_path)
			continue
		print("{} -> {}".format(source_path, target_path))
		os.rename(source_path, target_path)

		# common_prefix_length = 22 #TODO calculate this!
		# print("{prefix}{{{src} => {tgt}}}/{path}".format(
		# 	prefix=source[:common_prefix_length],
		# 	src=source[common_prefix_length:],
		# 	tgt=os.path.join(target, makemodel_dirname)[common_prefix_length:],
		# 	path=os.path.sep.join(relpath_parts)
		# ))

	print("Unknown (Make, Model):\n\t", "\n\t".join(map(str, makemodel_unknown)), sep="")


def sysmain(args=None):
	parser = argparse.ArgumentParser()
	parser.add_argument("--xxx", dest="xxx", action="store", metavar="VALUE", type=int, help="")
	opts = parser.parse_args(args)
	return main(opts)


if __name__ == '__main__':
	sys.exit(sysmain())
