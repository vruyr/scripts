promptmessage_default_style='\e[46;30m'
promptmessage_added_index=
declare -a promptmessage_rendered


declare -a _promptmessage_texts
declare -a _promptmessage_styles


function promptmessage_add() {
	local text="${1:-invalid usage of promptmessage_add}"
	local style="${2:-${promptmessage_default_style}}"
	_promptmessage_texts+=("$text")
	_promptmessage_styles+=("$style")
	idxs=("${!_promptmessage_texts[@]}")
	promptmessage_added_index="${idxs[@]: -1}"
	unset idxs
}


function promptmessage_remove() {
	for i in "$@"; do
		unset _promptmessage_texts[$i]
		unset _promptmessage_styles[$i]
	done
}


function promptmessage_set() {
	_promptmessage_texts["$1"]="$2"
	_promptmessage_styles["$1"]="$3"
}


function promptmessage_render_bash() {
	promptmessage_rendered=()
	local i
	for i in "${!_promptmessage_texts[@]}"; do
		promptmessage_rendered+=(
			' '
			'\['"${_promptmessage_styles[$i]}"'\]'
			"${_promptmessage_texts[$i]}"
			'\[\e[0m\]'
		)
	done
}
