declare -a _gitpromptmessage_previous_indexes

PROMPT_COMMAND="_gitpromptmessage_update${PROMPT_COMMAND:+; ${PROMPT_COMMAND}}"
function _gitpromptmessage_update() {
	promptmessage_remove "${_gitpromptmessage_previous_indexes[@]}"
	_gitpromptmessage_previous_indexes=()

	if git rev-parse --show-toplevel >/dev/null 2>&1; then
		local msg=$(git symbolic-ref --short -q HEAD || git rev-parse --short HEAD)
		promptmessage_add "HEAD:$msg"
		_gitpromptmessage_previous_indexes+=( "${promptmessage_added_index[@]}" )

		# if [ -n "$(git status --short)" ]; then
		# 	promptmessage_add "dirty"
		# 	_gitpromptmessage_previous_indexes+=( "${promptmessage_added_index[@]}" )
		# fi
	fi
}
