#!/usr/bin/env bash

set -o errexit

if [ -n "$1" ]; then
	cd "$1"
fi

old_IFS="$IFS"
IFS=$'\n'
files=( $(ls) )

for fn in "${files[@]}"; do
	fnn="$fn"
	fnn=${fnn//\:/%3A}
	fnn=${fnn//\?/%3F}
	fnn=${fnn//\//%2F}
	fnn=${fnn//\|/%7C}
	fnn=${fnn//\"/%22}
	if [ "$fn" == "$fnn" ]; then
		continue
	fi

	mv -v "$fn" "$fnn"
done
