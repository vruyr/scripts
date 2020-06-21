#!/usr/bin/env bash

supported_domains=(
	"youtube.com"
	"youtu.be"
)

set -o errexit

selfdir="$(cd "$(dirname "$0")" && pwd)"
download_folder=~/Downloads/youtube
destination_folder=/Volumes/Public/Videos/youtube
destination_git_folder=~/.xgit/videos

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
git -C "$destination_git_folder" status
if [ "$okay_dirty" != 1 ]; then
	git -C "$destination_git_folder" commit --allow-empty-message --no-edit
	git -C "$destination_git_folder" show HEAD --name-status
fi
