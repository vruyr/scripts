PYV_ROOT_DIR="${PYV_ROOT_DIR:-$HOME/.pyvenv}"

function pyv() {
	local default_file="$PYV_ROOT_DIR/.default"
	local venv_name=""
	if [ $# -eq 0 ]; then
		if [ ! -f "$default_file" ]; then
			echo "no venv name specified and no default configured" >&2
			return 1
		fi
		venv_name="$(cat "$default_file")"
	elif [ $# -eq 1 ]; then
		venv_name="$1"
	else
		echo "only one parameter please" >&2
		return 2
	fi
	local venv_dir="$PYV_ROOT_DIR/$venv_name"
	if [ ! -d "$venv_dir" ]; then
		echo "venv not found - ${venv_name}" >&2
		return 3
	fi

	source "$venv_dir/bin/activate"
}

function __pyv_complete() {
	# for v in $(compgen -A variable COMP); do echo "${v}=${!v}"; done
	COMPREPLY=()
	if [ ${COMP_CWORD} -ne 1 ]; then
		return
	fi
	local prefix="${PYV_ROOT_DIR%/}/"
	while [ "${prefix}" != "${prefix%/}" ]; do
		prefix="${prefix%/}"
	done
	local cur=${COMP_WORDS[COMP_CWORD]}
	local IFS=$'\n'
	COMPREPLY=(
		$(compgen -d "${prefix}/${cur}" | cut -b $(( ${#prefix} + 2 ))- )
	)
}

complete -F __pyv_complete pyv
