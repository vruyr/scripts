#!/usr/bin/env bash


getpocket delete $(
	getpocket list -d youtube.com | \
		grep $(
			printf ' -e https://www.youtube.com/watch?v=%q' $(
				for f in */*; do p='\.youtube\.([^.]+)\.[^.]+'; [[ "$f" =~ $p ]] && echo ${BASH_REMATCH[1]}; done
			)
		) | \
		cut -d $'\t' -f 1
)
