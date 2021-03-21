PYV_ROOT_DIR="${PYV_ROOT_DIR:-$HOME/.bin/python/venv}"


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


function pyv_new() {
	local python_path="$("$1" -c 'import sys, os; print(os.path.realpath(sys.executable))')"
	local pyvenv_name="$2"

	local pyvenv_root="$PYV_ROOT_DIR"
	local pyvenv_dir="$pyvenv_root/$pyvenv_name-$("$python_path" -c 'import platform; print(platform.python_implementation().lower(), "-", platform.python_version(), sep="")')"
	(
		set -o errexit
		printf "Creating the python venv '%s'\n" "$pyvenv_name"
		"$python_path" -m venv "$pyvenv_dir" --without-pip
		printf "Installing pip for '%s'\n" "$pyvenv_dir/bin/python"
		curl -s https://bootstrap.pypa.io/get-pip.py | "$pyvenv_dir/bin/python" -
	) >&2 || {
		echo >&1 "Python venv creation failed"
		return 1
	}
	printf "%s\n" "$pyvenv_dir"
	return 0
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


function __prompt_message_show_pyv() {
	if [ -z "$VIRTUAL_ENV" ]; then
		return
	fi
	python - "$VIRTUAL_ENV" "$HOME" <<-EOT
		from __future__ import print_function
		import os, sys
		path = sys.argv[1]
		base = sys.argv[2]
		relpath=os.path.relpath(path, base)
		print(relpath if not relpath.startswith(".." + os.path.sep) else path)
	EOT
}
