#!/usr/bin/env bash


set -o errexit
trap "echo FAILED" ERR


function main() {
	local path_before="$1"
	local path_after="$2"

	if [ -z "$path_before" -o -z "$path_after" ]; then
		echo "USAGE: $(basename "$0") <path_before> <path_after>" >&2
		exit 1
	fi

	if [ "${path_before: -1}" != "/" ]; then
		local path_before="$path_before/"
	fi

	local path_after="$(normalize_path "$path_after")"

	local IFS=$'\n'
	local did_show_target_file=
	for target_file in $(find_all_executable_files "$path_after"); do
		for library_path in $(list_required_libs "$target_file"); do
			startswith "$library_path" "$path_before" || continue
			echo "MATCH"

			local relative_path="${library_path:${#path_before}}"
			local num_folders_up="${target_file:${#path_after}}"
			local num_folders_up="${num_folders_up#/}"
			local num_folders_up="${num_folders_up//[^\/]}"
			local prefix=$(repeat_str "${#num_folders_up}" ../)

			if [ "$did_show_target_file" != 1 ]; then
				if [ -n "$did_show_target_file" ]; then
					echo
				fi
				echo "$target_file"
				local did_show_target_file=1
			fi

			local replacement_library_path="@loader_path/${prefix}$relative_path"

			printf '\t%q -> %q\n' "$library_path" "$replacement_library_path"
			install_name_tool -change "$library_path" "$replacement_library_path" "$target_file"
		done
		if [ "$did_show_target_file" == 1 ]; then
			local did_show_target_file=0
		fi
	done
}


function repeat_str() {
	local num="$1"
	local str="$2"
	[[ "$num" =~ ^[0-9]+$ ]] || {
		printf "Error: first parameter must be a positive integer: " >&2
		declare -p num >&2
		return 1
	}
	[ "$num" -eq 0 ] && return
	printf "%.0s$str" $(seq 1 "$num")
}


function startswith() {
	test "${1:0:${#2}}" == "$2"
}


function normalize_path() {
	cd "$1" && pwd
}


function list_required_libs() {
	local IFS=$'\n'
	local -a libs=(
		$(/Library/Developer/CommandLineTools/usr/bin/dyldinfo -dylibs "$1")
	)
	if [ "${libs[0]}" == "for arch x86_64:" ]; then
		unset libs[0]
		local libs=( "${libs[@]}" )
		declare -p libs
	fi
	if [ "${libs[0]}" != "attributes     dependent dylibs" ]; then
		echo "Unrecognized output from dyldinfo" >&2
		declare -p libs >&2
		return 1
	fi
	unset libs[0]

	local line_pattern='^[[:space:]]+([^[:space:]]+)$'
	for library_path in "${libs[@]}"; do
		if [[ "$library_path" =~ $line_pattern ]]; then
			echo "${BASH_REMATCH[1]}"
		else
			echo "Unrecognized output from dyldinfo" >&2
			declare -p library_path >&2
			return 1
		fi
	done
}


function find_all_executable_files() {
	local -a find_args=(
		-type f
		-not -name 'README'
		-not -name 'Makefile'
		-not -name '*.h'
		-not -name '*.html'
		-not -name '*.py'
		-not -name '*.pyc'
		-not -name '*.js'
		-not -name '*.txt'
		-not -name '*.xml'
		-not -name '*.png'
		-not -name '*.css'
		-not -name '*.plist'
		-not -name '*.tcl'
		-not -name '*.a'
		-not -name '*.rst'
		-not -name '*.c'
		-not -name '*.exe'
		-not -name '*.bat'
		-not -name '*.o'
		-not -name '*.sh'
		-not -name '*.zip'
		-not -name '*.aiff'
		-not -name '*.wav'
		-not -name '*.tar'
		-not -name '*.xsl'
		-not -name '*.dtd'
		-not -name '*.jpg'
		-not -name '*.bmp'
		-not -name '*.tiff'
		-not -name '*.gif'
		-not -name '*.fish'
		-not -name '*.csh'
		-not -name '*.ps1'
		-not -name '*.psm1'
		-not -name '*.pickle'
		-not -name '*.ico'
		-not -name '*.eps'
		-not -name '*.ini'
		-not -name '*.TXT'
		-not -name '*.wixproj'
		-not -name '*.sln'
		-not -name '*.vcxproj'
		-not -name '*.cpp'
		-not -name '*.doc'
		-not -name '*.decTest'
		-not -path '*/lib/tcl8.6/encoding/*.enc'
		-not -path '*/lib/tcl8.6/msgs/*.msg'
		-not -path '*/lib/tk8.6/msgs/*.msg'
		-not -path '*/share/doc/python*/examples/Tools/*/*.proj'
		-not -path '*/share/doc/python*/examples/Tools/*/*.props'
		-not -path '*/share/doc/python*/examples/Tools/*/*.wxs'
		-not -path '*/share/doc/python*/examples/Tools/*/*.wxl'
		-not -path '*/share/doc/python*/examples/Tools/*/*.wxl_template'
		-not -path '*/share/doc/python*/examples/Tools/*/*.nuspec'
	)

	local IFS=$'\n'
	for f in $(find "$1" "${find_args[@]}"); do
		local m="$(file --brief --mime-type "$f")"
		if [ "${m%%$'\n'*}" == "application/x-mach-binary" ]; then
			echo "$f"
		fi
	done
}


main "$@"
