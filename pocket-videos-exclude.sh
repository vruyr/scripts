#!/usr/bin/env bash

pocket-videos-list.sh | grep $(printf -- "-e %q " "$@") | pcre2grep -o '^\d+' | xargs getpocket tag -x _videos -t _videos_not -i
