#!/usr/bin/env bash

set -o errexit
trap "declare -p BASH_COMMAND; echo FAILED" ERR


   getpocket_path=getpocket
supported_domains=(
	"youtube.com"
	"youtu.be"
)


while [ $# -ne 0 ]; do
	case "$1" in
		"--getpocket-path")
			shift
			getpocket_path="$1"
			shift
			;;
		*)
			echo >&2 "Invalid Argument"
			exit 1
	esac
done


youtube_ids=($(
	for f in * */*; do p='\.youtube\.([^.]+)\.[^.]+'; [[ "$f" =~ $p ]] && echo ${BASH_REMATCH[1]}; done || true
))
item_ids=(
	$(
		"$getpocket_path" --dont-show-progress list $(printf " -d %q" "${supported_domains[@]}") | \
			grep $(
				printf ' -e ://www.youtube.com/watch?v=%q' "${youtube_ids[@]}"
				printf ' -e ://youtu.be/%q' "${youtube_ids[@]}"
			) | \
			cut -d $'\t' -f 1
	)
)
if [ "${#item_ids[@]}" -gt 0 ]; then
	"$getpocket_path" --dont-show-progress delete "${item_ids[@]}"
fi
