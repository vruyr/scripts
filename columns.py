#!/usr/bin/env python3

"""
Usage:
	{prog} (SEPARATOR_REGEX_PATTERN)...
"""

import sys, locale, os, re, functools, itertools
# pip install docopt==0.6.2
import docopt


def main(*, args, prog):
	locale.setlocale(locale.LC_ALL, "")

	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	patterns = params.pop("SEPARATOR_REGEX_PATTERN")
	assert not params, params

	sys.stdout.write(
		align_columns(
			text=sys.stdin.read(),
			column_patterns=patterns
		)
	)


def align_columns(*, text, column_patterns):
	rows = split_columns(text=text, column_patterns=column_patterns)
	widths = calculate_columns_widths(rows)
	def aligned_columns(rows):
		for row in rows:
			for width, column in itertools.zip_longest(widths[:len(row)], row, fillvalue=None):
				yield (column if ends_with_line_sep(column) else column.ljust(width))
	return "".join(aligned_columns(rows))


def calculate_columns_widths(rows):
	return list(functools.reduce(
		lambda c1, c2: [max(x) for x in itertools.zip_longest(c1, c2, fillvalue=0)],
		([len(c) for c in r] for r in rows)
	))


def split_columns(*, text, column_patterns):
	sep_p = re.compile("|".join(f"(?:{p})" for p in column_patterns))
	rows = []
	for line in text.splitlines(keepends=True):
		columns = []
		line_cursor = 0
		for sep_m in sep_p.finditer(line):
			column_start, column_end = sep_m.span()
			columns.append(line[line_cursor:column_start])
			columns.append(line[column_start:column_end])
			line_cursor = column_end
		columns.append(line[line_cursor:])
		rows.append(columns)
	return rows


def ends_with_line_sep(s):
	return s != s.splitlines(keepends=False)[-1]


def smain(argv=None):
	if argv is None:
		argv = sys.argv

	try:
		return main(
			args=argv[1:],
			prog=argv[0]
		)
	except KeyboardInterrupt:
		print(file=sys.stderr)


if __name__ == "__main__":
	sys.exit(smain())
