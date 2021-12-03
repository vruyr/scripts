#!/bin/sh

exec env -i SHELL=/bin/sh USER="$USER" PATH=/usr/bin:/bin PWD="$PWD" HOME="$HOME" LOGNAME="$LOGNAME" "$@"
