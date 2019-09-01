#!/usr/bin/env bash

item_ids=()


IFS=$'\t'
while read item_id given_url resolved_title; do
	resolved_title=${resolved_title//:/_}
	resolved_title=${resolved_title//\//_}

	# youtube-dl --format bestvideo+bestaudio --output "%(upload_date)s %(extractor)s-%(id)s [%(uploader)s] %(title)s.%(ext)s"
	youtube-dl --format bestvideo+bestaudio --output "%(upload_date)s %(duration) 5ds [%(uploader)s] ${resolved_title}.%(extractor)s.%(id)s.%(ext)s" "${given_url}"

	item_ids+=( "$item_id" )
done < <(getpocket list "$@" --format $'{item_id}\t{given_url}\t{resolved_title}\n')


printf "\n\n\n"
printf "getpocket delete"
printf " %q" "${item_ids[@]}"
printf "\n\n\n"
