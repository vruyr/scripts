#!/usr/bin/env bash

set -o errexit

trap "echo FAILED" ERR

thumbnail_png="thumbnail.png"
if [ -e "$thumbnail_png" ]; then
	echo >&2 "File with the name already exists, cant't move forward - $thumbnail_png"
	exit 1
fi

for thumbnail_orig in "$@"; do
	echo "$thumbnail_orig"
	if [ "$(git rev-parse --is-inside-work-tree)" == "true" ]; then
		git restore -s HEAD -S -- "$thumbnail_orig" || true
	fi
	filename_base="${thumbnail_orig%.*}"
	filename_video="$filename_base.mp4"
	ffmpeg -i "$thumbnail_orig" "$thumbnail_png"
	rm "$thumbnail_orig"
	AtomicParsley "$filename_video" --overWrite --artwork "$thumbnail_png"
	rm "$thumbnail_png"
done
