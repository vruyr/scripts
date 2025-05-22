#!/usr/bin/env python3

import pathlib, plistlib, datetime, dataclasses
from typing import Dict

BACKUP_DIR = pathlib.Path.home() / "Library" / "Application Support" / "MobileSync" / "Backup"

def gen_backup_infoplists():
	for dir_entry in BACKUP_DIR.iterdir():
		if not dir_entry.is_dir():
			continue
		i = dir_entry / "Info.plist"
		if not i.exists():
			continue
		yield i

@dataclasses.dataclass
class BackupInfo:
	last_backup_date: datetime.datetime
	serial_number: str
	device_name: str
	product_type: str
	product_version: str
	build_version: str
	product_name: str


backups: Dict[str, BackupInfo] = {}

for backup_infoplist in gen_backup_infoplists():
	with backup_infoplist.open("rb") as fo:
		backup_info = plistlib.load(fo)
	backup_name = backup_infoplist.parent.name

	# Apparently the datetimes read from a plist file are always UTC.
	# Reading the source code of plistlib module revealed a regex-based parser
	# that always expects a "Z" at the end of the datetime.

	backups[backup_name] = BackupInfo(
		last_backup_date=backup_info["Last Backup Date"].replace(tzinfo=datetime.timezone.utc).astimezone(),
		serial_number=backup_info["Serial Number"],
		device_name=backup_info["Device Name"],
		product_type=backup_info["Product Type"],
		product_version=backup_info["Product Version"],
		build_version=backup_info["Build Version"],
		product_name=backup_info["Product Name"],
	)


for (backup_name, backup) in sorted(backups.items(), key=lambda x: x[1].last_backup_date):
	print(
		backup_name.ljust(42),
		str(backup.last_backup_date).ljust(26),
		backup.serial_number.ljust(13),
		backup.device_name.ljust(6),
		backup.product_type.ljust(11),
		backup.product_version.ljust(7),
		backup.build_version.ljust(6),
		backup.product_name,
	)
