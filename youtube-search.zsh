#!/usr/bin/env zsh

youtube-search () {
	# See also: obsidian://open?vault=Comprehensive&file=New%2FStreaming%20Local%20Audio%20Files%20to%20a%20HomePod

	setopt local_options err_return

	local output_format=$'\e[100;97m\e]8;;%(webpage_url)s\a%(id)-11s\e]8;;\a\e[0m \e[42m%(upload_date>%Y-%m-%d)-10s\e[0m \e[103;30m%(view_count&{:>11,})s\e[0m \e[103;30m%(duration_string&{:>8})s\e[0m \e[46m%(uploader)-20s\e[0m %(title)s'
	local channel=() use_fzf= use_thumbnails= num_results_opt=()

	zparseopts -D -E -- c:=channel -channel:=channel -fzf=use_fzf t=use_thumbnails -thumbnails=use_thumbnails n:=num_results_opt -num-results:=num_results_opt

	local num_results=${num_results_opt[-1]:-0}

	local cmd_uv="$(command -v uv 2>/dev/null)"
	[[ -n "$cmd_uv" ]] || { print -u2 "youtube-search: missing dependency: uv"; return 1; }

	local search_query="$1"
	if [[ -z "$search_query" ]]; then
		read -r 'search_query?YouTube Search: '
	fi

	local source
	if [[ -n "$channel" ]]; then
		local handle="${channel[-1]}"
		[[ "$handle" != http* ]] && handle="https://www.youtube.com/$handle"
		source="${handle%/}/search?query=${search_query}"
	else
		if (( num_results > 0 )); then
			source="ytsearch${num_results}:${search_query}"
		else
			source="ytsearchall:${search_query}"
		fi
	fi

	local -a extra_opts=()
	[[ -n "$channel" && "$num_results" -gt 0 ]] && extra_opts=(--max-downloads "$num_results")

	local yt_cmd=("$cmd_uv" tool run -q yt-dlp@latest --no-warnings --skip-download --quiet "${extra_opts[@]}" --print "$output_format" "$source")

	if [[ -n "$use_thumbnails" ]]; then
		local cmd_timg="$(command -v timg 2>/dev/null)"
		local cmd_curl="$(command -v curl 2>/dev/null)"
		local cmd_sips="$(command -v sips 2>/dev/null)"
		local cmd_awk="$(command -v awk 2>/dev/null)"
		[[ -n "$cmd_timg" ]] || { print -u2 "youtube-search: missing dependency: timg"; return 1; }
		[[ -n "$cmd_curl" ]] || { print -u2 "youtube-search: missing dependency: curl"; return 1; }
		[[ -n "$cmd_sips" ]] || { print -u2 "youtube-search: missing dependency: sips"; return 1; }
		[[ -n "$cmd_awk"  ]] || { print -u2 "youtube-search: missing dependency: awk";  return 1; }

		local thumb_cols=40 thumb_rows=11
		local cell_height_px=20 cell_width_px=10  # defaults, overridden by terminal query below
		{
			local stty_save="$(stty -g </dev/tty)"
			stty -echo -icanon </dev/tty
			printf '\e[16t' >/dev/tty
			local cell_resp=
			IFS= read -d 't' -rs -t 1 cell_resp </dev/tty
			stty "$stty_save" </dev/tty
			local cell_parts=(${(s:;:)cell_resp})
			cell_height_px=${cell_parts[2]:-20}
			cell_width_px=${cell_parts[3]:-10}
		} 2>/dev/null || true

		local thumb_format=$'%(thumbnail)s\t%(webpage_url)s\t%(id)s\t%(upload_date>%Y-%m-%d)s\t%(view_count&{:,})s\t%(duration_string)s\t%(uploader)s\t%(title)s'

		"$cmd_uv" tool run -q yt-dlp@latest --no-warnings --skip-download --quiet \
			"${extra_opts[@]}" --print "$thumb_format" "$source" \
		| while IFS=$'\t' read -r thumbnail url id date views duration uploader title; do
			local tmp="/tmp/youtube-thumbnail-${id}"
			"$cmd_curl" -fsSL "$thumbnail" -o "$tmp" 2>/dev/null || { rm -f "$tmp"; continue; }
			local img_dims=($("$cmd_sips" -g pixelWidth -g pixelHeight "$tmp" 2>/dev/null | "$cmd_awk" '/pixel/{print $2}'))
			local img_w=${img_dims[1]:-0} img_h=${img_dims[2]:-0}
			local scaled_cols
			if (( img_w > 0 && img_h > 0 )); then
				scaled_cols=$(( (img_w * thumb_rows * cell_height_px + img_h * cell_width_px - 1) / (img_h * cell_width_px) ))
			else
				scaled_cols=$thumb_cols
			fi
			local info_col=$(( (scaled_cols < thumb_cols ? scaled_cols : thumb_cols) + 1 ))
			"$cmd_timg" -g "${thumb_cols}x${thumb_rows}" "$tmp"

			local today_epoch=$(date +%s)
			local video_epoch=$(date -j -f "%Y-%m-%d" "$date" +%s 2>/dev/null || date -d "$date" +%s)
			local days_ago=$(( (today_epoch - video_epoch) / 86400 ))
			local rel=
			if   (( days_ago <  7  )); then rel="${days_ago} days ago"
			elif (( days_ago <  30 )); then rel="$((days_ago / 7)) weeks ago"
			elif (( days_ago < 365 )); then rel="$((days_ago / 30)) months ago"
			else                            rel="$((days_ago / 365)) years ago"
			fi

			local -a info_lines=(
				$'\e]8;;'"${url}"$'\a\e[1m'"${title}"$'\e[0m\e]8;;\a'
				''
				"${duration}"
				''
				"${date}  (${rel})"
				''
				"${views} views"
				''
				"${uploader}"
				''
				"${id}"
			)
			printf "\e[${thumb_rows}A"
			for line in "${info_lines[@]}"; do
				printf "\e[${info_col}C%s\n" "$line"
			done
			(( thumb_rows > ${#info_lines[@]} )) && printf "\e[$((thumb_rows - ${#info_lines[@]}))B"
			printf "\n\n"
		done
		return
	fi

	local col_header=$("$cmd_uv" run --python 3 python -c "
import sys
h = {
	'webpage_url': '',
	'id': 'ID',
	'upload_date>%Y-%m-%d': 'DATE',
	'view_count&{:>11,}': '      VIEWS',
	'duration_string&{:>8}': 'DURATION',
	'uploader': 'UPLOADER',
	'title': 'TITLE',
}
import re
header = sys.argv[1] % h
width = len(re.sub(r'\x1b\[[^m]*m|\x1b\][^\a]*\a', '', header))
print(header)
print('─' * width)
" "$output_format")
	local fzf_height
	if (( num_results > 0 )); then
		fzf_height="$((num_results + 4))"
	else
		fzf_height="50%"
	fi

	local cmd_fzf="$(command -v fzf 2>/dev/null)"
	[[ -z "$use_fzf" || -n "$cmd_fzf" ]] || { print -u2 "youtube-search: missing dependency: fzf"; return 1; }

	if [[ -n "$use_fzf" ]]; then
		{ print -- "$col_header"; "${yt_cmd[@]}"; } \
			| "$cmd_fzf" --reverse --height="$fzf_height" --ansi --delimiter=' ' --accept-nth=1 --multi \
				  --header-lines=2
	else
		print -- "$col_header"
		"${yt_cmd[@]}"
	fi
}

# Run directly if executed as a script, not when sourced
[[ "$ZSH_EVAL_CONTEXT" == "toplevel" ]] && youtube-search "$@"
