#!/bin/sh

"$HOME/.bin/python/bin/python3" \
	$HOME/.bin/scripts/text2eml.py \
	--to="$MAILTO" \
	"$@" \
	-- \
	/usr/sbin/sendmail "$MAILTO"
