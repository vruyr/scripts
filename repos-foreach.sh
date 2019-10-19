#!/usr/bin/env bash


function main() {
	if [ $# -eq 0 ]; then
		set -- echo '$PWD'
	fi

	old_IFS="$IFS"
	IFS=$'\n'
	all_repos=(
		$(jq <~/.repos.json -r '.repositories[]')
	)
	IFS="$old_IFS"

	local r
	for r in "${all_repos[@]}"; do
		r="$HOME/$r"
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
	local color_ui=auto
	if [ -t 1 ]; then
		color_ui=always
	fi

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
		if [ -n "$(git -P log --oneline "${exclusions[@]}" --remotes="$r" "${nolocalrefs[@]}" -- )" ]; then
			l="$(git -c color.ui="$color_ui" -P gl --boundary "${exclusions[@]}" --remotes="$r" "${nolocalrefs[@]}" -- | sed $'s/^/\t\t/')"
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


function starts_with() {
	test "${1#$2}" != "$1"
}


main "$@"
