#!/usr/bin/env bash


set -o errexit


function main() {
	gitdir="$(git rev-parse --git-dir)"
	if [ -z "$gitdir" -o ! -d "$gitdir" ]; then
		echo 'FATAL: Failed to determine gitdir path.'
		exit 1
	fi

	if [ "$(git config --get core.bare)" == "true" ]; then
		check_refs

		if [ "$(cat "$gitdir/HEAD")" != "ref: refs/heads/master" ]; then
			echo 'FATAL: A bare repo with head not pointing to master is not supported'
			exit 1
		fi

		if [ "$(cd "$gitdir" && pwd)" != "$(pwd)" ]; then
			echo 'FATAL: Please `cd` to the root of the repo (detected git-dir: '"$gitdir"').'
			exit 1
		fi
	else
		worktree="$(git rev-parse --show-toplevel)"
		if [ -z "$worktree" -o ! -d "$worktree" ]; then
			echo 'FATAL: Failed to determine worktree path.'
			exit 1
		fi

		if [ "$(cd "$worktree" && pwd)" != "$(pwd)" ]; then
			echo 'FATAL: Please `cd` to the repo root folder first (detected worktree: '"$worktree"').'
			exit 1
		fi

		if [ -n "$(git status --porcelain=v2)" ]; then
			echo "FATAL: the worktree is not clean"
			exit 1
		fi

		if [ -n "$(git submodule foreach --recursive)" ]; then
			echo "FATAL: the worktree contains initialized submodules"
			exit 1
		fi

		#TODO Implement graceful deinit of submodules and recursive git-uninit.sh of "$gitdir/modules/*"

		check_refs
		empty_commit="$(create_empty_commit)"
		git checkout --quiet "$empty_commit"
		echo "ref: refs/heads/master" >"$(git rev-parse --git-path HEAD)"
	fi

	# The empty index will be holding back an empty tree object, we need to remove it first to git-gc the empty tree too.
	rm_if_sha1_matches ef73c107a70703d57b6512b4a7de6223d89faf09 "$gitdir/index"
	mkdir -p "$gitdir/objects/pack"
	git -c gc.reflogExpire=now -c gc.reflogExpireUnreachable=now gc --aggressive --prune=all --quiet

	# Generated by git-update-server-info and can be regenerated anytime
	rm_if_exists "$gitdir/objects/info/packs"

	# Unimporant files
	rm_if_exists "$gitdir/COMMIT_EDITMSG"
	rm_if_exists "$gitdir/FETCH_HEAD"
	rm_if_exists "$gitdir/ORIG_HEAD"

	# "ref: refs/heads/master"
	rm_if_sha1_matches acbaef275e46a7f14c1ef456fff2c8bbe8c84724 "$gitdir/HEAD"

	#TODO Instead of hardcoding sha sums, init a blank repo and remove every file that matches

	# zero length file
	rm_if_sha1_matches da39a3ee5e6b4b0d3255bfef95601890afd80709 "$gitdir/info/refs"

	# zero length file
	rm_if_sha1_matches da39a3ee5e6b4b0d3255bfef95601890afd80709 "$gitdir/logs/HEAD"

	# unmodified copies from the template
	rm_if_sha1_matches c879df015d97615050afa7b9641e3352a1e701ac "$gitdir/info/exclude"
	rm_if_sha1_matches 9635f1b7e12c045212819dd934d809ef07efa2f4 "$gitdir/description"
	rm_if_sha1_matches ee1ed5aad98a435f2020b6de35c173b75d9affac "$gitdir/hooks/commit-msg.sample"
	rm_if_sha1_matches 5885a56ab4fca8075a05a562d005e922cde9853b "$gitdir/hooks/pre-rebase.sample"
	rm_if_sha1_matches 288efdc0027db4cfd8b7c47c4aeddba09b6ded12 "$gitdir/hooks/pre-rebase.sample"
	rm_if_sha1_matches 36aed8976dcc08b5076844f0ec645b18bc37758f "$gitdir/hooks/pre-commit.sample"
	rm_if_sha1_matches 33729ad4ce51acda35094e581e4088f3167a0af8 "$gitdir/hooks/pre-commit.sample"
	rm_if_sha1_matches 86b9655a9ebbde13ac8dd5795eb4d5b539edab0f "$gitdir/hooks/applypatch-msg.sample"
	rm_if_sha1_matches 4de88eb95a5e93fd27e78b5fb3b5231a8d8917dd "$gitdir/hooks/applypatch-msg.sample"
	rm_if_sha1_matches 2b6275eda365cad50d167fe3a387c9bc9fedd54f "$gitdir/hooks/prepare-commit-msg.sample"
	rm_if_sha1_matches 2584806ba147152ae005cb675aa4f01d5d068456 "$gitdir/hooks/prepare-commit-msg.sample"
	rm_if_sha1_matches b614c2f63da7dca9f1db2e7ade61ef30448fc96c "$gitdir/hooks/post-update.sample"
	rm_if_sha1_matches 42fa41564917b44183a50c4d94bb03e1768ddad8 "$gitdir/hooks/pre-applypatch.sample"
	rm_if_sha1_matches b4ad74c989616b7395dc6c9fce9871bb1e86dfb5 "$gitdir/hooks/pre-push.sample"
	rm_if_sha1_matches 5c8518bfd1d1d3d2c1a7194994c0a16d8a313a41 "$gitdir/hooks/pre-push.sample"
	rm_if_sha1_matches 39355a075977d05708ef74e1b66d09a36e486df1 "$gitdir/hooks/update.sample"
	rm_if_sha1_matches e729cd61b27c128951d139de8e7c63d1a3758dde "$gitdir/hooks/update.sample"
	rm_if_sha1_matches f7c0aa40cb0d620ff0bca3efe3521ec79e5d7156 "$gitdir/hooks/fsmonitor-watchman.sample"
	rm_if_sha1_matches f208287c1a92525de9f5462e905a9d31de1e2d75 "$gitdir/hooks/pre-applypatch.sample"
	rm_if_sha1_matches 705a17d259e7896f0082fe2e9f2c0c3b127be5ac "$gitdir/hooks/pre-receive.sample"

	# "# pack-refs with: peeled fully-peeled sorted"
	rm_if_sha1_matches b87768695bbfa0ff94952151224ddeb01ed48767 "$gitdir/packed-refs"

	rmdir_empty_recursively "$gitdir/refs/"
	rmdir_if_exists "$gitdir/refs/"

	rmdir_empty_recursively "$gitdir/logs/"
	rmdir_if_exists "$gitdir/logs/"

	rmdir_if_exists "$gitdir/info/"
	rmdir_if_exists "$gitdir/hooks/"

	rmdir_if_exists "$gitdir/objects/info/"
	rmdir_if_exists "$gitdir/objects/pack/"
	rmdir_if_exists "$gitdir/objects/"

	git config -f "$gitdir/config" --unset core.repositoryformatversion || true
	git config -f "$gitdir/config" --unset core.filemode                || true
	git config -f "$gitdir/config" --unset core.bare                    || true
	git config -f "$gitdir/config" --unset core.logallrefupdates        || true
	git config -f "$gitdir/config" --unset core.ignorecase              || true
	git config -f "$gitdir/config" --unset core.precomposeunicode       || true
	
	git config -f "$gitdir/config" --unset push.default || true

	# TODO Unhardcode this
	git config -f "$gitdir/config" --unset user.name '^Vruyr Gyolchanyan$' || true
	git config -f "$gitdir/config" --unset user.email '^vruyr@vruyr.com$'  || true

	# zero length file
	rm_if_sha1_matches da39a3ee5e6b4b0d3255bfef95601890afd80709 "$gitdir/config"

	if [ "$gitdir" != "." ]; then
		rmdir "$gitdir"
	fi

	tree -FACa
}


function create_empty_commit() {
	local empty_tree="$(git hash-object -w -t tree /dev/null)"
	export GIT_AUTHOR_DATE="1544709284 +0000"
	export GIT_AUTHOR_NAME=A
	export GIT_AUTHOR_EMAIL=A
	export GIT_COMMITTER_DATE="1544709284 +0000"
	export GIT_COMMITTER_NAME=A
	export GIT_COMMITTER_EMAIL=A
	local empty_commit="$(git commit-tree "$empty_tree" </dev/null)"
	test "$empty_commit" == "ee9ed328ba60087830351deb77df613f87f846f0" || {
		echo "FATAL: Created empty commit does not match expectations"
		exit 1
	}
	printf "%s\n" "$empty_commit"
}


function check_refs() {
	all_refs="$(git for-each-ref --format="%(refname)")"
	if [ -n "$all_refs" ]; then
		echo "FATAL: Before proceeding please make sure all references are deleted"
		return 1
	fi
}


function rm_if_sha1_matches() {
	local oldsha1="$1"
	local filepath="$2"
	if [ -z "$oldsha1" -o ! -e "$filepath" ]; then
		return 0
	fi
	local newsha1="$(cat "$filepath" | openssl dgst -sha1)"
	if [ -n "$newsha1" -a "$newsha1" == "$oldsha1" ]; then
		rm_if_exists "$filepath"
	fi
	return 0
}


function rm_if_exists() {
	local filepath="$1"
	if [ -f "$filepath" ]; then
		rm -f "$filepath" || :
	fi
}


function rmdir_empty_recursively() {
	local dirpath="$1"
	if [ ! -d "$dirpath" ]; then
		return
	fi
	local IFS=$'\n'
	while true; do
		local empty_dirs=(
			$(find "$dirpath" -depth -mindepth 1 -type d -empty)
		)
		if [ "${#empty_dirs[@]}" -gt 0 ]; then
			rmdir "${empty_dirs[@]}"
		else
			break
		fi
	done
}


function rmdir_if_exists() {
	local dirpath="$1"
	if [ -d "$dirpath" ]; then
		rmdir "$dirpath" || :
	fi
}


main "$@"
