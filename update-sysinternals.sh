#!/usr/bin/env bash

set -o errexit

url="https://guest@live.sysinternals.com/"
mount_point="/Volumes/live.sysinternals.com/"

if [ ! -e "${mount_point}" ]; then
	echo "Mounting ${url}"
	osascript -e 'tell application "Finder" to mount volume "https://live.sysinternals.com/"'
fi

srcdir="${mount_point}/Tools"
dstdir="$HOME/Documents/Software/SysInternals"
rsync_args=(
	--recursive
	--checksum
	--times
	--verbose
	--delete-after
	--exclude=web.config
)

rsync "${rsync_args[@]}" "${srcdir}/" "${dstdir}/"

hdiutil eject "${mount_point}"
