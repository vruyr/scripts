#!/bin/bash

tmux=/workopt/vruyr/apps/linux-2.6.32-glibc-2.12-x86_64/tmux/1.7/bin/tmux

test "$COLORTERM" == "gnome-terminal" -a -z "$TMUX" && export TERM=gnome-256color
$tmux has-session &>/dev/null && exec $tmux attach || exec $tmux

#if $tmux has-session &>/dev/null;
#then
#	exec $tmux attach
#else
#	ssh -x $(hostname) $tmux' new-session -d'
#	exec $tmux attach \; new-window \; last-window \; kill-window \; move-window -t 1
#	# all this shenanigans with window creation and killing is needed to have the DISPLAY set correctly
#fi
