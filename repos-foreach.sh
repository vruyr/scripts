#!/usr/bin/env bash


color_ui=auto
if [ -t 1 ]; then
	color_ui=always
fi


function main() {
	if [ $# -eq 0 ]; then
		set -- echo '$PWD'
	fi

	old_IFS="$IFS"
	IFS=$'\n'
	all_repos=(
		$(jq <~/.repos.json -r '.repositories[]' | tr -d '\r')
	)
	IFS="$old_IFS"

	local r
	for r in "${all_repos[@]}"; do
		r="$(cd "$HOME" && cd "$r" && pwd)"
		local w="$(command git -C "$r" rev-parse --show-toplevel)"
		local w=${w:-${r%/.git}}
		(
			if [ "${r#"$w"}" != ".git" ]; then
				export GIT_DIR="$r"
			fi
			cd "$w"
			eval "$@"
		)
	done
}


function incoming() {
	local url_prefixes=( "$@" )

	at_least_one_not_skipped=
	at_least_one_skipped=
	output_messages=()
	for r in `git remote`; do
		u="$(git remote get-url "$r")"

		local must_skip=1
		if [ ${#url_prefixes[@]} -eq 0 ]; then
			must_skip=
		else
			local url_prefix=
			for url_prefix in "${url_prefixes[@]}"; do
				if starts_with "$u" "$url_prefix" || starts_with "${HOME}${u#\~}" "$url_prefix"; then
					must_skip=
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
		old_IFS="$IFS"
		IFS=$'\n'
		excluded_refs=(
			$(git config --get-all "remote.$r.repos-ignore-refs" | sed 's|^refs/heads/||')
		)
		IFS="$old_IFS"
		for exref in "${excluded_refs[@]}"; do
			exclusions+=( "--exclude" "$r/$exref" )
		done

		git fetch --prune -q "$r"
		old_IFS="$IFS"
		IFS=$'\n'
		local -a nolocalrefs=(
			$(printf "\n^%s" $(git show-ref | grep -v " refs/remotes/" | cut -b -40))
		)
		IFS="$old_IFS"

		any_new_tags="$(git fetch --prune --prune-tags --tags --dry-run "$r" 2>&1 | sed $'s/^/\t\t/')"

		if [ -n "$any_new_tags" ]; then
			output_messages+=( $'\n' "$any_new_tags" )
		fi

		if [ -n "$(git -P log --oneline "${exclusions[@]}" --remotes="$r" "${nolocalrefs[@]}" -- )" ]; then
			l="$(git -c color.ui="$color_ui" -P lg --boundary "${exclusions[@]}" --remotes="$r" "${nolocalrefs[@]}" -- | sed $'s/^/\t\t/')"
			output_messages+=( "$(printf "\n\t%s\n%s\x1b[0m\n" "$r" "$l")" )
		fi
	done

	if [ -n "$at_least_one_not_skipped" -a -z "$at_least_one_skipped" ]; then
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
		echo >&2 "USAGE: repos-foreach.sh object-type <object_nameish>"
		return 1
	fi
	local object_nameish="$1"; shift

	local object_type="$(git cat-file -t "$object_nameish" 2>/dev/null)"
	if [ $? -ne 0 -o -z "$object_type" ]; then
		return 0
	fi

	local object_sha="$(git rev-parse "$object_nameish")"

	printf "%s\t%s\t%s\n" "$object_sha" "$object_type" "$(pwd)"
}


temp_output_lines_num_displayed=0


function temp_output_lines_printf() {
	[ -t 1 ] || return

	printf "$@"
	(( temp_output_lines_num_displayed++ ))
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
		echo >&2 "USAGE: repos-foreach.sh object-type <object_nameish>"
		return 1
	fi
	local object_nameish="$1"; shift

	temp_output_lines_printf 'Searching in %s\n' "$PWD"
	object_name="$(git rev-parse --quiet --verify "$object_nameish^{object}")"
	if [ $? -eq 0 -a -n "$object_name" ]; then
		#TODO The --find-object option is incapable of finding commit trees. Sub-trees are okay.
		local log_output="$(git -c color.ui="$color_ui" --no-pager log --raw --find-object="$object_name" 2>&1)"
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
	test "${1#$2}" != "$1"
}


main "$@"
