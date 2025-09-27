# gh api repos/org/repo/pulls/(PR_NUMBER)/comments

def add_anchor($url):
	"\u001B]8;;\($url)\u0007\(.)\u001B]8;;\u0007";

def reaction_to_emoji:
	{
		"+1":        "👍",
		"-1":        "👎",
		"laugh":     "😄",
		"hooray":    "🎉",
		"confused":  "😕",
		"heart":     "❤️",
		"rocket":    "🚀",
		"eyes":      "👀"
	}[.];

def render_comment_reactions:
	.reactions
	| delpaths([
		["url"],
		["total_count"]
	])
	| to_entries
	| [.[] | select(.value != 0)]
	| map("\(.key | reaction_to_emoji) \(.value)")
	| join(" ");


map(.rendered_id =
	(if .in_reply_to_id == null
	then "\(.id)"
	else "\(.in_reply_to_id):\(.id)"
	end)
)
| sort_by([.rendered_id, .created_at])
| .[]
| . as $comment
| if .in_reply_to_id == null then
	.indent_lines = ""
else
	.indent_lines = "\t"
	| .body |= (split("\n") | map("\t" + .) | join("\n"))
end
| (
	"\(.indent_lines)" +
	"\u001B[47;30m" +
	("\(.created_at) \(.in_reply_to_id):\(.id) \(.user.login) \(.path):\(.line)" | add_anchor($comment.html_url)) +
	"\u001B[0m" + "\n" +
	"\(.body)" +
	"\n" +
	"\(.indent_lines)\($comment | render_comment_reactions)\n"
)
