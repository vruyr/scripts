#!/usr/bin/env bash

set -o errexit

color_ui=auto
if [ -t 1 ]; then
	color_ui=always
fi


function main() {
	if [ $# -eq 0 ]; then
		set -- pwd
	fi

	local show_path=
	if [ "$1" == "--show" ]; then
		show_path=1
		shift
	fi

	all_repos=()
	while IFS='' read -r line; do [ "$line" ] && all_repos+=("$line"); done < <(
		jq <~/.rgit.json -r '.repositories[]' | tr -d '\r'
	)
	unset line

	IFS=':' read -ra extra_search_roots <<< "${RGITFOREACHROOTS}"

	if [ "${#extra_search_roots[@]}" -gt 0 ]; then
		while IFS='' read -r line; do [ "$line" ] && all_repos+=("$line"); done < <(
			find "${extra_search_roots[@]}" -type f -name HEAD -execdir sh -c 'test -d objects -a -d refs && pwd' \; -prune
		)
		unset line
	fi

	local r
	for r in "${all_repos[@]}"; do
		r="$(cd "$HOME" && cd "$(git --git-dir "$r" rev-parse --git-path .)" && pwd)"
		(
			local curdir
			if [ "$(git -C "$r" --git-dir "$r" config --get --bool core.bare)" == "false" ]; then
				local w
				w="$(git -C "$r" config --default "${r%/.git}" --get core.worktree)"
				if [ "${r#"$w"}" != ".git" ]; then
					export GIT_DIR="$r"
				fi
				curdir="$w"
			else
				curdir="$r"
			fi

			cd "$curdir"
			if [ -n "$show_path" ]; then
				echo "$curdir"
			fi
			"$@" || :
		)
	done
}


function incoming() {
	local -a url_prefixes_include
	local -a url_prefixes_exclude

	for i in "$@"; do
		if [ "${i:0:1}" == "-" ]; then
			url_prefixes_exclude+=( "${i:1}" )
		else
			url_prefixes_include+=( "$i" )
		fi
	done

	if [ "${PWD}" != "${PWD%/.git}" ]; then
		cd ..
	fi

	at_least_one_not_skipped=
	at_least_one_skipped=
	output_messages=()
	for r in $(git remote); do
		u="$(git remote get-url "$r")"

		local must_skip=1
		if [ ${#url_prefixes_include[@]} -eq 0 ]; then
			must_skip=
		else
			local url_prefix=
			for url_prefix in "${url_prefixes_include[@]}"; do
				if starts_with "$u" "$url_prefix" || starts_with "${HOME}${u#\~}" "$url_prefix"; then
					must_skip=
					break
				fi
			done
		fi

		if [ -z "$must_skip" ]; then
			for url_prefix in "${url_prefixes_exclude[@]}"; do
				if starts_with "$u" "$url_prefix" || starts_with "${HOME}${u#\~}" "$url_prefix"; then
					must_skip=1
					break
				fi
			done
		fi

		if [ -n "$must_skip" ]; then
			at_least_one_skipped=1
			continue
		fi

		at_least_one_not_skipped=1

		exclusions=()
		excluded_refs=()
		while IFS='' read -r line; do [ "$line" ] && excluded_refs+=("$line"); done < <(
			git config --get-all "remote.$r.rgit-ignore-refs" | sed 's|^refs/heads/||'
		)
		unset line
		for exref in "${excluded_refs[@]}"; do
			exclusions+=( "--exclude" "$r/$exref" )
		done

		git fetch --prune -q "$r"
		local -a exclude_local_refs=()
		while IFS='' read -r line; do [ "$line" ] && exclude_local_refs+=("^$line"); done < <(
			git show-ref | grep -v " refs/remotes/" | cut -b -40
		)
		unset line

		any_new_tags="$(git fetch --prune --prune-tags --tags --dry-run "$r" 2>&1 | sed $'s/^/\t\t/')"

		if [ -n "$any_new_tags" ]; then
			output_messages+=( $'\n' "$any_new_tags" )
		fi

		if [ -n "$(git -P log --oneline "${exclusions[@]}" --remotes="$r" "${exclude_local_refs[@]}" -- )" ]; then
			l="$(git -c color.ui="$color_ui" -P lg -10 --boundary "${exclusions[@]}" --remotes="$r" "${exclude_local_refs[@]}" -- | sed $'s/^/\t\t/')"
			output_messages+=( "$(printf "\n\t%s\n%s\x1b[0m\n" "$r" "$l")" )
		fi
	done

	if [ -n "$at_least_one_not_skipped" ] && [ -z "$at_least_one_skipped" ]; then
		if [ "${#output_messages[@]}" -ne 0 ]; then
			printf "%s%s %s%s\n" $'\x1b[0;42;30m' '•' "$(pwd)" $'\x1b[0m'
			printf "%s" "${output_messages[@]}"
			printf "\n"
		else
			printf "%s%s %s%s\n" $'\x1b[0m' '•' "$(pwd)" $'\x1b[0m'
		fi
	else
		if [ -n "$at_least_one_not_skipped" ]; then
			if [ "${#output_messages[@]}" -ne 0 ]; then
				printf "%s%s %s%s\n" $'\x1b[0;2;32m' 'P' "$(pwd)" $'\x1b[0m'
				printf "%s" "${output_messages[@]}"
				printf "\n"
			else
				printf "%s%s %s%s\n" $'\x1b[0;37m' 'P' "$(pwd)" $'\x1b[0m'
			fi
		else
			printf "%s%s %s%s\n" $'\x1b[0;2;37m' 'S' "$(pwd)" $'\x1b[0m'
		fi
	fi
}


function object-type() {
	if [ "$#" -ne 1 ]; then
		echo >&2 "USAGE: rgit-foreach.sh object-type <object_nameish>"
		return 1
	fi
	local object_nameish="$1"; shift

	local object_type
	if ! object_type="$(git cat-file -t "$object_nameish" 2>/dev/null)" || [ -z "$object_type" ]; then
		return 0
	fi

	local object_sha
	object_sha="$(git rev-parse "$object_nameish")"

	printf "%s\t%s\t%s\n" "$object_sha" "$object_type" "$(pwd)"
}


temp_output_lines_num_displayed=0


function temp_output_lines_printf() {
	[ -t 1 ] || return

	#shellcheck disable=SC2059
	printf "$@"
	(( temp_output_lines_num_displayed++ )) || true
}


function temp_output_lines_clear() {
	[ -t 1 ] || return

	if [ "$temp_output_lines_num_displayed" -gt 0 ]; then
		printf '\x1b[%dF\x1b[0J' "$temp_output_lines_num_displayed"
	fi
	temp_output_lines_num_displayed=0
}


function find-object() {
	if [ "$#" -ne 1 ]; then
		echo >&2 "USAGE: rgit-foreach.sh object-type <object_nameish>"
		return 1
	fi
	local object_nameish="$1"; shift

	temp_output_lines_printf 'Searching in %s\n' "$PWD"
	if object_name="$(git rev-parse --quiet --verify "$object_nameish^{object}")" && [ -n "$object_name" ]; then
		#TODO The --find-object option is incapable of finding commit trees. Sub-trees are okay.
		local log_output=""
		log_output+="$(git cat-file -t "$object_name")"$'\n'
		log_output+="$(git -c color.ui="$color_ui" --no-pager log --all --graph --decorate --raw --find-object="$object_name" 2>&1)"
		temp_output_lines_clear
	else
		temp_output_lines_clear
		return
	fi

	if [ "$log_output" == "error: unable to resolve '$object_name'" ]; then
		return
	fi

	if [ -n "$log_output" ]; then
		printf '%s\n' "$PWD"
		printf '\t%s\n' "${log_output//$'\n'/$'\n\t'}"
	fi
}


function starts_with() {
	test "${1#"$2"}" != "$1"
}


main "$@"
