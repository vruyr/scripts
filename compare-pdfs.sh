#!/usr/bin/env bash


MAGICK=magick
MAGICK_DENSITY=300


function main() {
	local selfname=$(basename "$0")
	if [ $# -ne 3 ]; then
		printf >&2 "Usage:\n"
		printf >&2 "    %q one.pdf two.pdf diff.pdf\n" "$selfname"
		return 1
	fi

	local workdir=$(mktemp -d -t "${selfname}")
	trap "rmdir \"${workdir}\"" RETURN

	local one="$1"
	local two="$2"
	local diff="$3"

	if [ -e "$diff" ]; then
		printf >&2 "Refusing to overwrite %q\n" "$diff"
		return 2
	fi

	printf >&2 "Enumerating pages of %q\n" "$one"
	IFS=$'\n' one_pages=(
		$($MAGICK identify -format '%[input][%p]\n' "$one")
	)

	printf >&2 "Enumerating pages of %q\n" "$two"
	IFS=$'\n' two_pages=(
		$($MAGICK identify -format '%[input][%p]\n' "$two")
	)

	if [ "${#one_pages[@]}" -ne "${#two_pages[@]}" ]; then
		echo >&2 "Two PDFs being compared must have the same number of pages."
		return 3
	fi

	declare -a diff_pages

	printf >&2 "Comparing %s pages" "${#one_pages[@]}"
	local diff_page
	for ((i=0; i<"${#one_pages[@]}"; i++)) do
		diff_page="$workdir/diff-$i.pdf"
		printf >&2 "."
		$MAGICK compare -density "$MAGICK_DENSITY" "${one_pages[$i]}" "${two_pages[$i]}" "$diff_page"
		diff_pages+=(
			"$diff_page"
		)
	done
	printf >&2 "\n"

	printf >&2 "Writing %q\n" "$diff"
	$MAGICK convert "${diff_pages[@]}" "$diff"

	rm "${diff_pages[@]}"
	printf "%s" "$diff"
	printf >&2 "\n"
}



main "$@"
