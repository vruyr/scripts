#!/usr/bin/env bash

set -o errexit

selfdir="$(cd "$(dirname "$0")" && pwd)"
download_folder=~/Downloads/youtube
destination_folder=/Volumes/Public/Videos/youtube
destination_git_folder=~/.xgit/videos

finish_existing=
while [ $# -ne 0 ]; do
	case "$1" in
		"--finish-existing")
			finish_existing=1
			shift
			;;
		*)
			echo >&2 "Invalid Argument"
			exit 1
	esac
done

test -d "$destination_folder" || {
	echo 2>&1 "Please mount the destination folder before proceeding."
	exit 1
}

if [ -e "$download_folder" ]; then
	echo 2>&1 "WARNING: Reusing an already existing download folder:"
	tree 2>&1 -aNF "${download_folder}"
else
	mkdir -p "$download_folder"
fi
cd "$download_folder"
if [ -z "$finish_existing" ]; then
	getpocket list "$@" -d youtube.com -x _videos_not --format $'{resolved_url}\n' | youtube-dl -a -
fi
rsync --size-only --recursive --partial --progress "${download_folder}/" "${destination_folder}/"
cd "${download_folder}"
old_IFS="$IFS"
IFS=$'\n'
all_files=( $(find . -type f) )
IFS="$old_IFS"
unset old_IFS
for f in "${all_files[@]}"; do
	if [ -e "${destination_folder}/$f" ]; then
		git -C "$destination_git_folder" add -v "${destination_folder}/$f"
		rm -v "${download_folder}/$f"
	fi
done
cd ..
rmdir "${download_folder}"/*
rmdir "${download_folder}"
cd "${destination_folder}/"
"$selfdir/pocket-videos-remove-downloaded.sh"
git -C "$destination_git_folder" status
