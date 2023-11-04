#!/usr/bin/env zsh

ssh_remote_command_and_args=(
	tmux -CC -u

	start-server

	'\;'

	set-option -g 
		default-terminal "${(q)TERM}"

	'\;'

	new-session -A 
		-s iterm2
		-e LC_TERMINAL="${(q)LC_TERMINAL}"
		-e LC_TERMINAL_VERSION="${(q)LC_TERMINAL_VERSION}"
)

exec ssh \
	-o "RemoteCommand ${(j: :)ssh_remote_command_and_args[@]}" \
	-o 'RequestTTY yes' \
	"$@"
