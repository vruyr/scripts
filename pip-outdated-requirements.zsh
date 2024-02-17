#!/usr/bin/env zsh

pip_args=(
	install
	--upgrade
	--requirement requirements.txt
	--dry-run
	--report -
	--quiet
	--force-reinstall
)


jq_script='
	.install
	| map("\(.metadata.name)==\(.metadata.version)")
	| sort[]
'


jq_script_2='
	.install[]
	| delpaths([
		["download_info", "url"],
		["download_info", "archive_info", "hash"],
		["download_info", "archive_info", "hashes", "sha256"],
		["metadata", "classifier"],
		["metadata", "description"],
		["metadata", "platform"],
		["metadata", "project_url"],
		["metadata", "description_content_type"],
		["metadata", "home_page"],
		["metadata", "license"],
		["metadata", "author_email"],
		["metadata", "author"],
		["metadata", "summary"],
		["metadata", "requires_python"],
		["metadata", "maintainer"],
		["metadata", "maintainer_email"],
		["metadata", "keywords"]
	])
'

# ./bin/pip "${pip_args[@]}" | jq -r "$jq_script_2"
# exit

diff --color=auto -U100 \
	<(./bin/pip freeze | sort) \
	<(./bin/pip "${pip_args[@]}" | jq -r "$jq_script")
