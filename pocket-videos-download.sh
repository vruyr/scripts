#!/usr/bin/env bash

supported_domains=(
	"youtube.com"
	"youtu.be"
)

set -o errexit

selfdir="$(cd "$(dirname "$0")" && pwd)"
       download_folder="$(python3 -c 'import sys,pathlib;print(str(pathlib.Path(sys.argv[1]).absolute()))'        "${download_folder:-$HOME/Downloads/youtube}")"
    destination_folder="$(python3 -c 'import sys,pathlib;print(str(pathlib.Path(sys.argv[1]).absolute()))'     "${destination_folder:-/Volumes/Public/Videos/youtube}")"
destination_git_folder="$(python3 -c 'import sys,pathlib;print(str(pathlib.Path(sys.argv[1]).absolute()))' "${destination_git_folder:-$HOME/.xgit/videos}")"


okay_dirty=
finish_existing=
while [ $# -ne 0 ]; do
	case "$1" in
		"--finish-existing")
			finish_existing=1
			shift
			;;
		"--okay-dirty")
			okay_dirty=1
			shift
			;;
		*)
			echo >&2 "Invalid Argument"
			exit 1
	esac
done

test -d "$destination_folder" || {
	echo 2>&1 "Please mount the destination folder before proceeding."
	exit 1
}

test "$okay_dirty" == 1 -o -z "$(git -C "$destination_git_folder" status --porcelain=v2)" || {
	echo 2>&1 "The repository is dirty."
	exit 1
}

if [ -e "$download_folder" ]; then
	echo 2>&1 "WARNING: Reusing an already existing download folder:"
	tree 2>&1 -aNF "${download_folder}"
else
	mkdir -p "$download_folder"
fi
cd "$download_folder"
if [ -z "$finish_existing" ]; then
	declare -a urls=(
		$(getpocket list "$@" $(printf " -d %q" "${supported_domains[@]}") -x _videos_not --format $'{resolved_url}\n')
	)
	declare -p urls
	if [ "${#urls[@]}" -gt 0 ]; then
		printf "%s\n" "${urls[@]}" | youtube-dl -i -a - || true
	fi
fi
find . -type f \( -name '*.webp' -o -name '*.jpg' \) -exec pocket-videos-finish-embedding-thumbnails.sh {} +
unrecognized_files="$(find . -type f -not -name '*.mp4' -not -name .DS_Store )"
if [ -n "$unrecognized_files" ]; then
	echo "UNRECOGNIZED FILES:"
	echo "$unrecognized_files"
	exit 1
fi
rsync --size-only --recursive --partial --progress "${download_folder}/" "${destination_folder}/"
cd "${download_folder}"
old_IFS="$IFS"
IFS=$'\n'
all_files=( $(find . -type f -not -name .DS_Store) )
IFS="$old_IFS"
unset old_IFS
for f in "${all_files[@]}"; do
	if [ -e "${destination_folder}/$f" ]; then
		git -C "$destination_git_folder" add -v "${destination_folder}/$f"
		rm -v "${download_folder}/$f"
	fi
done
cd ..
rrmdir "${download_folder}"
cd "${destination_folder}/"
"$selfdir/pocket-videos-remove-downloaded.sh"

p='^[0-9]{8} \[([^]]+)\] .*'
for f in *; do
	[[ "$f" =~ $p ]] || continue
	d="${BASH_REMATCH[1]}"
	if [ -d "$d" ]; then
		git mv --force "$f" "$d/"
	elif [ -f ".routes/$d" ]; then
		dd="$(cat ".routes/$d")"
		if [ -n "$dd" ]; then
			mkdir -p "$dd"
			git mv --force "$f" "$dd/"
		fi
	fi
done

git -C "$destination_git_folder" status
if [ "$okay_dirty" != 1 ]; then
	diff_index_expected=":000000 100644 0000000000000000000000000000000000000000 e69de29bb2d1d6434b8b29ae775ad8c2e48c5391 A"
	diff_index="$(git -C "$destination_git_folder" diff-index --cached --raw HEAD | cut -d $'\t' -f 1 | sort -u)"
	if [ "$diff_index" == "$diff_index_expected" ]; then
		git -C "$destination_git_folder" commit --allow-empty-message --no-edit
		git -C "$destination_git_folder" show HEAD --name-status
	else
		echo "WARNING: Refusing to commit anything to git as some content is not trimmed to empty files."
	fi
fi
