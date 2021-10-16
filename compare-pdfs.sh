#!/usr/bin/env bash


MAGICK=magick
MAGICK_DENSITY=300
MAGICK_LOWLIGHT_COLOR="rgba(255,255,255,0.95)"


set -o errexit


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

	local num_pages="${#one_pages[@]}"

	declare -a diff_pages

	local msg='Compared %s of %s pages %s'
	printf >&2 "$msg" 0 $num_pages $'\n'
	local diff_page
	for ((i=0; i < "$num_pages"; i++)) do
		diff_page="$workdir/diff-$i.pdf"
		#TODO Find out why magick compare exits with non-zero exit code
		$MAGICK compare -lowlight-color "$MAGICK_LOWLIGHT_COLOR" -density "$MAGICK_DENSITY" "${one_pages[$i]}" "${two_pages[$i]}" "$diff_page" || true
		diff_pages+=(
			"$diff_page"
		)
		set_message 1 "$(printf "$msg" "$(( i + 1 ))" "$num_pages" "$(render_progress_bar $(( i + 1 )) "$num_pages" 27)")"
	done

	printf >&2 "Writing %q\n" "$diff"
	$MAGICK convert -density "$MAGICK_DENSITY" "${diff_pages[@]}" "$diff"

	rm "${diff_pages[@]}"
	printf "%s" "$diff"
	printf >&2 "\n"
}


function set_message() {
	local msg_num="$1"
	local msg="$2"
	if [[ ! "$msg_num" =~ ^[0-9]+$ ]]; then
		printf '%q: First parameter must be an integer.\n' "set_message"
		return 1
	fi
	printf '\e[%sF\e[2K' "$msg_num"
	if [ -n "$msg" ]; then
		printf '%s' "$msg"
	fi
	printf '\e[%sE' "$msg_num"
}


function render_progress_bar() {
	local value="$1"
	local total="$2"
	local width="$3"
	if [ $# -ne 3 ]; then
		printf >&2 '%q: Expecting 3 parameters - value total width.\n' "render_progress_bar"
		return 1
	fi
	if [[ ! "$value" =~ ^[0-9]+$ || ! "$total" =~ ^[0-9]+$ || ! "$width" =~ ^[0-9]+$ ]]; then
		printf >&2 '%q: All parameters must be an integers.\n' "render_progress_bar"
		return 1
	fi

	bp=$(( ( value * 10000 ) / total ))

	frame_start='['
	frame_end='] %3d%%'
	frame_width=7

	porgress_bar_char_filled='#'
	porgress_bar_char_empty='-'
	porgress_bar_width=$(( width - frame_width ))
	porgress_bar_filled=$(( porgress_bar_width * bp / 10000 ))
	porgress_bar_empty=$(( porgress_bar_width - porgress_bar_filled ))

	printf "$frame_start"
	for ((i=0; i < "$porgress_bar_filled"; i++)) do
		printf '%s' "$porgress_bar_char_filled"
	done
	for ((i=0; i < "$porgress_bar_empty"; i++)) do
		printf '%s' "$porgress_bar_char_empty"
	done
	printf "$frame_end" $(( bp / 100 ))
}


main "$@"
