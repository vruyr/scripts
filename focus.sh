#!/bin/bash

xprop -root -spy _NET_ACTIVE_WINDOW | while read id; 
do
	id=${id##* }
	now=$(date "+%Y-%m-%d %H:%M:%S")	

	echo -n "$now <Window ID: $id> "

	test $id == "0x0" && { echo; continue; }

	title=$(xprop -id $id WM_NAME); title=${title#* = }
	pid=$(xprop -id ${id} _NET_WM_PID); pid=${pid##* }; 

	echo -n "$title $(readlink /proc/$pid/exe) "

	# additional argument to bash is ommited intentionally to exclude executable name
	cat /proc/$pid/cmdline | cut -d $'\0' -f 2- | tr -d '\n' | xargs -0r bash -c 'printf "%q " "$@"' ''

	echo
done
