#!/bin/sh

SELFDIR="$(cd "$(dirname "$0")" && pwd)"
"$SELFDIR/pstree.py" -c "$(cut -d "$(printf '\t')" -f 1 </usr/share/firmlinks | tr '\n' '\0' | xargs -0 printf "^%s|" $() | sed 's/|$//')"
