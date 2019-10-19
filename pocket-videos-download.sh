#!/usr/bin/env bash


if [ "$#" -eq 0 ]; then
	set -- -d youtube.com
fi


item_ids=()


IFS=$'\t'
while read item_id given_url resolved_title; do
	resolved_title=${resolved_title//\:/%3A}
	resolved_title=${resolved_title//\?/%3F}
	resolved_title=${resolved_title//\//%2F}
	resolved_title=${resolved_title//\|/%7C}
	resolved_title=${resolved_title//\"/%22}

	youtube-dl \
		--embed-thumbnail \
		--format 'bestvideo[ext=mp4]+bestaudio[ext=m4a]' \
		--output "%(uploader)s/%(upload_date)s ${resolved_title}.%(extractor)s.%(id)s.%(ext)s" \
		"${given_url}"

	item_ids+=( "$item_id" )
done < <(getpocket list "$@" --format $'{item_id}\t{given_url}\t{resolved_title}\n')


printf "\n\n\n"
printf "getpocket delete"
printf " %q" "${item_ids[@]}"
printf "\n\n\n"
