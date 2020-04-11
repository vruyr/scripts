#!/usr/bin/env bash


supported_domains=(
	"youtube.com"
	"youtu.be"
)
youtube_ids=($(
	for f in */*; do p='\.youtube\.([^.]+)\.[^.]+'; [[ "$f" =~ $p ]] && echo ${BASH_REMATCH[1]}; done
))
item_ids=(
	$(
		getpocket list $(printf " -d %q" "${supported_domains[@]}") | \
			grep $(
				printf ' -e ://www.youtube.com/watch?v=%q' "${youtube_ids[@]}"
				printf ' -e ://youtu.be/%q' "${youtube_ids[@]}"
			) | \
			cut -d $'\t' -f 1
	)
)
if [ "${#item_ids[@]}" -gt 0 ]; then
	getpocket delete "${item_ids[@]}"
fi
