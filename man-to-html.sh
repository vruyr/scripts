#!/usr/bin/env bash

man_file_abs_path="$(man -w "$1")"
declare -p man_file_abs_path

if ! [ -f "$man_file_abs_path" ]; then
	printf "Failed to find man file path for %q" "$1"
	exit 1
fi

man_dir="${man_file_abs_path%/*/*}"
declare -p man_dir

if ! [ -d "$man_dir" ]; then
	printf "Failed to identify the man dir for %q - %q" "$man_file_abs_path" "$man_dir"
	exit 1
fi

cur_dir="$(pwd)"

html_file_path="${cur_dir}/${man_file_abs_path##*/}.html"
declare -p html_file_path

printf '\n\n'

cd "$man_dir" || exit
groff -m mandoc -Thtml <"$man_file_abs_path" >"${html_file_path}"
