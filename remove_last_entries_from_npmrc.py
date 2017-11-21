#!/usr/bin/env python3

import sys

removals = set(sys.argv[1:])

lines = sys.stdin.read().splitlines(False)
while len(lines) and len(removals) and removals != [""]:
	x = lines[-1].strip().split("=", -1)[0]
	if x in removals:
		lines.pop()
		removals.remove(x)
	else:
		break
while len(lines):
	if not lines[-1].strip():
		lines.pop()
	else:
		break

print("\n".join(lines), end="\n")
