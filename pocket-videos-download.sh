#!/usr/bin/env bash

set -o errexit
trap "declare -p BASH_COMMAND; echo FAILED" ERR


function abspath() {
	python3 -c 'import sys, pathlib; print(str(pathlib.Path(sys.argv[1]).absolute()))' "$1"
}


            selfdir="$(cd "$(dirname "$0")" && pwd)"
    git_repo_folder="$(abspath "${git_repo_folder:-$HOME/.xgit/videos}")"
git_worktree_folder="$(git rev-parse --show-toplevel)"
        root_folder=
    download_folder=
         okay_dirty=
    finish_existing=
           is_dirty=
     getpocket_path=getpocket
          tree_path=tree
     youtubedl_path=youtube-dl
  supported_domains=(
	"youtube.com"
	"youtu.be"
)


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
		"--getpocket-path")
			shift
			getpocket_path="$1"
			shift
			;;
		"--tree-path")
			shift
			tree_path="$1"
			shift
			;;
		"--youtubedl-path")
			shift
			youtubedl_path="$1"
			shift
			;;
		*)
			echo >&2 "Invalid Argument"
			exit 1
	esac
done



getpocket_extra_args=()
youtubedl_extra_args=()
if ! [ -t 2 ]; then
	getpocket_extra_args=( --dont-show-progress )
	youtubedl_extra_args=( --no-progress )
fi


root_folder="$(pwd)"
while [ "$root_folder" != "/" -a ! -d "$root_folder/.routes" ]; do
	root_folder="$(dirname "$root_folder")"
done
if [ ! -d "$root_folder/.routes" ]; then
	echo 2>&1 "Can not find the \".routes\" folder. Aborting."
	exit 1
fi

detected_git_repo_folder="$(abspath "$(git -C "$git_worktree_folder" rev-parse --git-dir)")"
if [ "$git_repo_folder" != "$detected_git_repo_folder" ]; then
	declare >&2 -p git_worktree_folder git_repo_folder detected_git_repo_folder
	echo >&2 "Failed to identify git repository and/or worktree folders. Aborting."
	exit 1
fi
unset detected_git_repo_folder

function this_git() {
	git --git-dir="$git_repo_folder" --work-tree="$git_worktree_folder" "$@"
}


is_dirty="$(this_git status --porcelain=v2)"
test "$okay_dirty" == 1 -o -z "$is_dirty" || {
	echo 2>&1 "The repository is dirty."
	exit 1
}


download_folder="$root_folder/.tmp"
if [ -e "$download_folder" ]; then
	echo 2>&1 "WARNING: Reusing an already existing download folder:"
	"$tree_path" 2>&1 -aNF "${download_folder}"
else
	mkdir -p "$download_folder"
fi
cd "$download_folder"


if [ -z "$finish_existing" ]; then
	declare -a urls=(
		$("$getpocket_path" "${getpocket_extra_args[@]}" list "$@" $(printf " -d %q" "${supported_domains[@]}") -x _videos_not --format $'{resolved_url}\n')
	)
	if [ "${#urls[@]}" -gt 0 ]; then
		declare -p urls
		printf "%s\n" "${urls[@]}" | "$youtubedl_path" >&2 "${youtubedl_extra_args[@]}" -i -a - || true
	fi
	unset urls
fi
find . -type f \( -name '*.webp' -o -name '*.jpg' \) -exec "$selfdir/pocket-videos-finish-embedding-thumbnails.sh" {} +
unrecognized_files="$(find . -type f -not -name '*.mp4' -not -name .DS_Store )"
if [ -n "$unrecognized_files" ]; then
	echo "UNRECOGNIZED FILES:"
	echo "$unrecognized_files"
	exit 1
fi
unset unrecognized_files


old_IFS="$IFS"
IFS=$'\n'
downloaded_files=( $(find . -type f -not -name .DS_Store) )
IFS="$old_IFS"
unset old_IFS
for f in "${downloaded_files[@]}"; do
	mv -v "$f" "$root_folder/$f"
	this_git add -v "$root_folder/$f"
done
unset downloaded_files f


cd "$root_folder"
RRMDIR_QUIET=1 "$selfdir/rrmdir" "${download_folder}"


"$selfdir/pocket-videos-remove-downloaded.sh" --getpocket-path "$getpocket_path"


p='^[0-9]{8} \[([^]]+)\] .*'
for f in *; do
	[[ "$f" =~ $p ]] || continue
	d="${BASH_REMATCH[1]}"
	if [ -d "$d" ]; then
		this_git mv --force "$f" "$d/"
	elif [ -f ".routes/$d" ]; then
		dd="$(cat ".routes/$d")"
		if [ -n "$dd" ]; then
			mkdir -p "$dd"
			this_git mv -v --force "$f" "$dd/"
		fi
	fi
done
unset p f d dd

if [ "$okay_dirty" != 1 -a -n "$(this_git diff-index --cached --raw HEAD)" ]; then
	this_git status
	diff_index_expected=":000000 100644 0000000000000000000000000000000000000000 e69de29bb2d1d6434b8b29ae775ad8c2e48c5391 A"
	diff_index="$(this_git diff-index --cached --raw HEAD | cut -d $'\t' -f 1 | sort -u)"
	if [ "$diff_index" == "$diff_index_expected" ]; then
		this_git commit --allow-empty-message --no-edit
		this_git show HEAD --name-status
	else
		echo "WARNING: Refusing to commit anything to git as some content is not trimmed to empty files."
	fi
	unset diff_index_expected diff_index
fi
