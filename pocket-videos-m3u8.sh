#!/usr/bin/env bash

supported_domains=(
	"youtube.com"
)

echo "#EXTM3U"
getpocket list "$@" \
	--format $'{given_url}\n' \
	$(printf " -d %q" "${supported_domains[@]}") \
	| \
	youtube-dl --batch-file=- --dump-json --format=best | \
	jq -r '"#EXTINF:" + (.duration|tostring) + "," + .uploader + " - " + .title + " " + .id + "\n" + .url'
