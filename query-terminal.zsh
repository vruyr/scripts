#!/usr/bin/env zsh

query_terminal_luminance() {
	local response_for_low="${1:-low}"
	local response_for_high="${2:-high}"

	exec {ttyfd}<>/dev/tty

	if [[ ! -t "${ttyfd}" ]]; then
		return 1
	fi

	local stty_cfg_old="$(stty -g <&"$ttyfd")"
	local -a stty_cfg_new=(
		raw     # Disables canonical mode (line buffering/editing) so input is passed directly.
		-echo   # Prevents echoing characters back to the terminal.
		min 0   # Allows read to return immediately even with 0 characters (non-blocking).
		time 1  # Sets a 0.1-second timeout for read to avoid hanging if no response.
	)
	stty "${stty_cfg_new[@]}" <&"$ttyfd"
	unset stty_cfg_new

	# https://www.xfree86.org/current/ctlseqs.html
	# https://iterm2.com/documentation-escape-codes.html
	# https://xtermjs.org/docs/api/vtfeatures/#osc
	# https://en.wikipedia.org/wiki/ANSI_escape_code

	local response
	echo -n $'\e]11;?\e\\'  >&"$ttyfd"
	read -r response        <&"$ttyfd"

	# Expected result: $'\e]11;rgb:hhhh/hhhh/hhhh\e\\'

	stty "$stty_cfg_old" <&"$ttyfd"
	unset stty_cfg_old

	local expected_prefix=$'\e]11;rgb:'
	if [[ ! "${response:0:${#expected_prefix}}" == "$expected_prefix" ]]; then
		return 2
	fi
	# Remove the prefix.
	response=${response:${#expected_prefix}}

	# Remove OSC sequence finalizer
	response=${response%%$'\e\\'}  # Either ST  (0x1B 0x5C)
	response=${response%%$'\x9C'}  # Or     ST  (0x9C)
	response=${response%%$'\a'}    # Or     BEL (0x07)

	local -a rgb=( "${(s:/:)response}" )
	# Ensure we have exactly three components (r, g, b)
	[[ "${#rgb[@]}" -eq 3 ]] || return 3

	local num_hex_digits=$(( ($#response - 2) / 3 ))
	(( num_hex_digits < 1 || num_hex_digits > 4 )) && return 4
	local max_color_value=$(( 16**num_hex_digits - 1 ))

	local r g b
	r=$(( 16#${rgb[1]} ))
	g=$(( 16#${rgb[2]} ))
	b=$(( 16#${rgb[3]} ))

	# https://www.w3.org/TR/WCAG20/relative-luminance.xml
	local luminance=$(( (2126 * r + 7152 * g + 722 * b) / 10000 ))
	# 2126 + 7152 + 722 = 10000

	if (( luminance > (max_color_value / 2) )) then
		echo "$response_for_high"
	else
		echo "$response_for_low"
	fi
}

if [[ "${zsh_eval_context[-1]}" == "toplevel" ]]; then
	case "$1" in
		luminance)
			query_terminal_luminance "$2" "$3"
			exit $?
			;;
		*)
			echo "Usage: ${0:t} (COMMAND) [ARGS...]" >&2
			exit 1
			;;
	esac
fi
