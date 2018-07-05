#!/usr/bin/env bash


folders=(
	$(brew --cache)
	~/Library/Caches/pip
)

du -hsc "${folders[@]}"
