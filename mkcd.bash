function mkcd() {
	test -n "$1" -a ! -e "$1" && { mkdir "$1" && cd "$1"; } || echo 'No way!';
}
