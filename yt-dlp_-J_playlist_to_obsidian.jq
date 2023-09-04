(now | strflocaltime("%FT%T%z") | "\(.[0:-2]):\(.[-2:])") as $ts
|
(
	"- YouTube [\(.channel)](https://www.youtube.com/channel/\(.channel_id)) Playlist [\(.title)](\(.webpage_url)) [added::\($ts)] [BUG::The timezone is incorrect - doesn't consider DST.]"
	|
	.
)
,
(
	"\t- [\(.channel)](https://www.youtube.com/channel/\(.channel_id))" as $prefix
	|
	.entries | sort_by(.playlist_index) | .[]
	|
	"\($prefix) \(.upload_date[0:4])-\(.upload_date[4:6])-\(.upload_date[6:8]) [\(.title)](\(.webpage_url)) (\(.duration_string))"
	|
	.
)
