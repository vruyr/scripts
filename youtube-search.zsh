#!/usr/bin/env zsh

youtube-search () {
    setopt local_options err_return
    local output_format=$'\e[100;97m\e]8;;%(webpage_url)s\a%(id)-11s\e]8;;\a\e[0m \e[42m%(upload_date>%Y-%m-%d)-10s\e[0m \e[103;30m%(view_count&{:>11,})s\e[0m \e[103;30m%(duration_string&{:>8})s\e[0m \e[46m%(uploader)-20s\e[0m %(title)s'
    local channel=() use_fzf= num_results_opt=()

    zparseopts -D -E -- c:=channel -channel:=channel -fzf=use_fzf n:=num_results_opt -num-results:=num_results_opt

    local num_results=${num_results_opt[-1]:-0}

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

    local yt_cmd=(uv tool run -q yt-dlp@latest --no-warnings --skip-download --quiet "${extra_opts[@]}" --print "$output_format" "$source")

    local col_header=$(uv run --python 3 python -c "
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

    if [[ -n "$use_fzf" ]]; then
        { print -- "$col_header"; "${yt_cmd[@]}"; } \
            | fzf --reverse --height="$fzf_height" --ansi --delimiter=' ' --accept-nth=1 --multi \
                  --header-lines=2
    else
        print -- "$col_header"
        "${yt_cmd[@]}"
    fi
}

# Run directly if executed as a script, not when sourced
[[ "$ZSH_EVAL_CONTEXT" == "toplevel" ]] && youtube-search "$@"
