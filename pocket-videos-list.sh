#!/usr/bin/env bash

supported_domains=(
	"youtube.com"
	"youtu.be"
)

getpocket list "$@" \
	--format $'{tag_list}\t{item_id}\t{given_url}\t{resolved_title}\n' \
	$(printf " -d %q" "${supported_domains[@]}") \
	| \
	column -t -s $'\t' | \
	sort | \
	sed 's|https://www.youtube.com/watch?v=|youtu.be/|g; s|https://m.youtube.com/watch?v=|youtu.be/|g; s|https://youtu.be/|youtu.be/|g;'
