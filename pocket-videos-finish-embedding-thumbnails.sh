#!/usr/bin/env bash

set -o errexit

trap "echo FAILED" ERR

for thumbnail_orig in "$@"; do
	echo "$thumbnail_orig"
	git restore -s HEAD -S -- "$thumbnail_orig"
	filename_base="${thumbnail_orig%.*}"
	filename_video="$filename_base.mp4"
	thumbnail_png="${filename_base}.png"
	ffmpeg -i "$thumbnail_orig" "$thumbnail_png"
	rm "$thumbnail_orig"
	AtomicParsley "$filename_video" --overWrite --artwork "$thumbnail_png"
	rm "$thumbnail_png"
done
