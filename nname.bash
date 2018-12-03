function nname() {
	local length="${1:-5}"
	local name=$(pwgen --no-capitalize --no-numerals --num-passwords=1 "$length")
	case "$(uname -s)" in
		Darwin*)
			echo -n "$name" | pbcopy
			;;
		CYGWIN*|MINGW*)
			echo -n "$name" | clip
			;;
		Linux*)
			echo >&2 "Clipboard is support is not implemented on Linux."
			;;
		*)
			echo >&2 "Clipboard is support is not implemented - platform unknown."
			;;
	esac
	echo "$name"
}
