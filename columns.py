#!/usr/bin/env uv --quiet run --script --
# /// script
# # Docopt issues SyntaxWarning in Python 3.12
# requires-python = ">=3.11,<3.12"
# dependencies = [
#   "docopt >=0.6.2",
# ]
# ///

"""
Usage:
	{prog} (-s REGEX)... [--] [FILE]...
	{prog} (-r REGEX)    [--] [FILE]...

Options:
	--separator, -s REGEX  The regular expression for the column separator.
	--row, -r REGEX        The regular expression for the entire row where columns are capture groups. Lines that do not match will be ignored.
"""

import sys, locale, os, re, functools, itertools
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
	params.pop("--")
	files = params.pop("FILE")
	separator_patterns = params.pop("--separator")
	row_pattern = params.pop("--row")
	assert (len(separator_patterns) == 0) != (row_pattern is None), (separator_patterns, row_pattern)
	assert not params, params

	if row_pattern:
		column_splitter = functools.partial(split_columns_by_row_pattern, pattern=row_pattern)
	else:
		column_splitter = functools.partial(split_columns_by_separator, patterns=separator_patterns)

	if files:
		text = ""
		for f in files:
			with open(f, "r") as fo:
				text += fo.read()
	else:
		text = sys.stdin.read()

	sys.stdout.write(
		align_columns(
			text=text,
			column_splitter=column_splitter
		)
	)


def align_columns(*, text, column_splitter):
	lines = text.splitlines(keepends=True)
	rows = column_splitter(lines=lines)
	widths = calculate_columns_widths(rows)
	def aligned_columns(rows):
		for row in rows:
			for width, column in itertools.zip_longest(widths[:len(row)], row, fillvalue=None):
				yield (column if ends_with_line_sep(column) else align_text(column, width) + "")
	return "".join(aligned_columns(rows))


def calculate_columns_widths(rows):
	if not rows:
		return []
	widths = [[len(strip_ansi_escapes(c)) for c in r] for r in rows]
	return list(functools.reduce(
		lambda c1, c2: [max(x) for x in itertools.zip_longest(c1, c2, fillvalue=0)],
		widths
	))


def align_text(text, width):
	text_len = len(strip_ansi_escapes(text))
	return text + " " * (max(width, text_len) - text_len)


def strip_ansi_escapes(s):
	return ANSI_ESCAPE_PATTERN.sub("", s)


# 7-bit C1 ANSI sequences
ANSI_ESCAPE_PATTERN = re.compile(r"""
    \x1B          # ESC
    (?:           # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |             # or [ for CSI, followed by a control sequence
        \[
        [0-?]*    # Parameter bytes
        [ -/]*    # Intermediate bytes
        [@-~]     # Final byte
    )
""", re.VERBOSE)


def split_columns_by_separator(*, lines, patterns):
	sep_p = re.compile("|".join(f"(?:{p})" for p in patterns))
	rows = []
	for line in lines:
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


def split_columns_by_row_pattern(*, lines, pattern):
	p = re.compile(pattern, flags=re.DOTALL)
	rows = []
	for line in lines:
		m = p.fullmatch(line)
		if m is None:
			raise ValueError("not all lines match the row regular expression")
		rows.append(m.groups(default=""))
	return rows


def ends_with_line_sep(s):
	return s and s != s.splitlines(keepends=False)[-1]


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
