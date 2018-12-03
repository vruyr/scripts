__cdp_prefix=~/Projects/
function cdp() {
	test "$#" -gt 1 && { echo "Error: Only one argument is supported at this moment."; return; }
	cd "$__cdp_prefix""$@"
}

function __cdp_complete() {
	local cur=${COMP_WORDS[COMP_CWORD]}
	local IFS=$'\n'
	COMPREPLY=( $( compgen -S/ -d ${__cdp_prefix}${cur} | cut -b $(( ${#__cdp_prefix} + 1 ))- ) )
}

complete -o nospace -o filenames -F __cdp_complete cdp


#TODO Introduce a common generator instead of copy pasting.


function cdr() {
	local prefix_dir="$(git rev-parse --show-toplevel)/"
	test "$#" -gt 1 && { echo "Error: Only one argument is supported at this moment."; return; }
	cd "${prefix_dir}""$@"
}

function __cdr_complete() {
	local prefix_dir="$(git rev-parse --show-toplevel)/"
	local cur=${COMP_WORDS[COMP_CWORD]}
	local IFS=$'\n'
	COMPREPLY=( $( compgen -S/ -d ${prefix_dir}${cur} | cut -b $(( ${#prefix_dir} + 1 ))- ) )
}

complete -o nospace -o filenames -F __cdr_complete cdr
