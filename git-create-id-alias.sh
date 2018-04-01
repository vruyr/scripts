#!/usr/bin/env bash
git config --global alias.id "$(tail -n+4 "$0")" && git config --global alias.id
exit
!function show_or_set_id() {
	if [ "$#" -eq 0 ]; then
		(
			printf '%s\t%s\n' user.name "$(git config --get --null --show-origin user.name | tr '\0' '\t')"
			printf '%s\t%s\n' user.email "$(git config --get --null --show-origin user.email | tr '\0' '\t')"
		) | column -t -s $'\t'

		echo "Contributors:"
		git --no-pager  log --all --format=tformat:'%an <%ae>%n%cn <%ce>' | sort -u | sed 's/^/'$'\t''/'

		if [ "$(git config --global --get --bool user.useconfigonly)" != "true" -o "$(git config --global --get user.name)" == ""  -o "$(git config --global --get user.email)" != "" ]; then
			echo
			echo "WARNING: User identity is configured incorrectly. Run the following commands to fix it:"
			echo "         git config --global user.useConfigOnly true"
			echo "         git config --global user.name \"$(finger $(whoami) | awk '/Name:/ {print $4" "$5}')\""
			echo "         git config --global --unset user.email"
		fi
	elif [ "$#" -eq 1 ]; then
		git config --local user.email "$1"
	else
		echo "USAGE: git id [email-to-set]" >&2
	fi
}
show_or_set_id
