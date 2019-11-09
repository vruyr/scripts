#!/usr/bin/env bash

set -o errexit

selfdir="$(cd "$(dirname "$0")" && pwd)"
download_folder=~/Downloads/youtube
destination_folder=/Volumes/Public/Videos/youtube

test -d "$destination_folder" || {
	echo 2>&1 "Please mount the destination folder before proceeding."
	exit 1
}

if [ -e "$download_folder" ]; then
	echo 2>&1 "WARNING: Reusing an already existing download folder: ${download_folder}"
else
	mkdir -p "$download_folder"
fi
cd "$download_folder"
getpocket list "$@" -d youtube.com -x _videos_not --format $'{resolved_url}\n' | youtube-dl -a -
rsync --size-only --recursive --partial --progress "${download_folder}/" "${destination_folder}/"
cd "${destination_folder}/"
"$selfdir/pocket-videos-delete-downloaded.sh"
