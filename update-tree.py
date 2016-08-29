#!/usr/bin/env python3

import sys, argparse, re, functools, datetime, locale


def main(argv=None):
	opts = _parse_args(argv=argv)
	with opts.filepath:
		text = opts.filepath.read()

	root  = Node("<root>", lineno=None, prefix=None)
	previous_node = None

	line_pattern = r"^(\s*)(Estimate:\s*)(.*)(\s*)$"

	for lineno, line in enumerate(text.splitlines()):
		parts = re.match(line_pattern, line)
		if not parts:
			continue

		prefix, label, value, suffix = parts.groups()
		node = Node(value, lineno=lineno, prefix=prefix)

		if not previous_node:
			previous_node = root.add_child(node)
		elif previous_node.prefix == node.prefix:
			previous_node = previous_node.add_sibling(node)
		elif len(previous_node.prefix) < len(node.prefix):
			previous_node = previous_node.add_child(node)
		else:
			while not (len(previous_node.prefix) < len(node.prefix)) and previous_node.parent is not None:
					previous_node = previous_node.parent
			previous_node = previous_node.add_child(node)

	root.update_aggregates(parser=parse_duration, aggregator=(lambda x, y: x + y))
	# show_tree(root)
	# return
	updates = tree_to_line_dict(root)

	for lineno, line in enumerate(text.splitlines()):
		if lineno not in updates:
			print(line)
			continue
		new_value = updates[lineno]
		prefix, label, value, suffix = re.match(line_pattern, line).groups()
		print(prefix, label, new_value, suffix, sep="")


time_duration_pattern = re.compile(
	(
		r"^\s*"
		r"(?:(?P<weeks>"   r"\d+)\s*W)?\s*"
		r"(?:(?P<days>"    r"\d+)\s*D)?\s*"
		r"(?:(?P<hours>"   r"\d+)\s*H)?\s*"
		r"(?:(?P<minutes>" r"\d+)\s*M)?\s*"
		r"(?:(?P<seconds>" r"\d+)\s*S)?\s*"
		r"\s*$"
	),
	flags=re.I
)
def parse_duration(duration):
	m = re.match(time_duration_pattern, duration)
	if m is None:
		return None
	parts = dict((key, int(value)) for key, value in m.groupdict().items() if value is not None)
	return datetime.timedelta(**parts)


def show_tree(node, *, indent="\t", depth=0):
	result = [timedelta_to_str(value) if isinstance(value, datetime.timedelta) else str(value) for value in node._aggregate_value]
	result = " + ".join(result)
	print(indent * depth + str(node.value), "|", result)
	for child in node.children:
		show_tree(child, indent=indent, depth=(depth + 1))


def tree_to_line_dict(node):
	result_dict = {}
	result_value = [timedelta_to_str(value) if isinstance(value, datetime.timedelta) else str(value) for value in node._aggregate_value]
	result_value = " + ".join(result_value)
	result_dict[node.lineno] = result_value
	for child in node.children:
		result_dict.update(tree_to_line_dict(child))
	return result_dict


def timedelta_to_str(timedelta):
	if timedelta is None:
		return None

	seconds = int(timedelta.total_seconds())
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)

	result = []
	if hours:
		result.append("{}h".format(hours))
	if minutes:
		result.append("{}m".format(minutes))
	if seconds:
		result.append("{}s".format(seconds))

	return " ".join(result)


class Node(object):
	def __init__(self, value, *, lineno, prefix, parent=None):
		self._value = value
		self._lineno = lineno
		self._prefix = prefix
		self._parent = parent
		self._children = []

		self._aggregate = None
		self._aggregate_value = None

	@property
	def lineno(self):
		return self._lineno

	@property
	def prefix(self):
		return self._prefix


	@property
	def parent(self):
		return self._parent

	@property
	def children(self):
		return (node for node in self._children)

	@property
	def value(self):
		return self._value

	def add_child(self, node):
		node._parent = self
		self._children.append(node)
		return node

	def add_sibling(self, node):
		return self.parent.add_child(node)

	def last_child(self):
		return self._children[-1]

	def update_aggregates(self, *, parser, aggregator):
		self._aggregate = []
		if not self._children:
			self._aggregate.append(self.value)
		else:
			for child in self._children:
				child.update_aggregates(parser=parser, aggregator=aggregator)
				self._aggregate.extend(child._aggregate)

		if not self._aggregate:
			self._aggregate_value = self._aggregate
			return

		the_aggregate = None
		not_aggregated = []
		for value in self._aggregate:
			parsed_value = parser(value)
			if parsed_value is None:
				not_aggregated.append(value)
			elif the_aggregate is None:
				the_aggregate = parsed_value
			else:
				the_aggregate = aggregator(the_aggregate, parsed_value)

		if the_aggregate is not None:
			not_aggregated.insert(0, the_aggregate)
		self._aggregate_value = not_aggregated



def _parse_args(argv=None):
	parser = argparse.ArgumentParser(
		prog=(argv[0] if argv is not None else None),
		description=None,
		epilog=None
	)
	parser.add_argument("filepath", nargs="?", metavar="PLAINTASKS_FILE", type=argparse.FileType("r"), default=sys.stdin)
	opts = parser.parse_args((argv[1:] if argv is not None else None))
	return opts


if __name__ == "__main__":
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		print(file=sys.stderr)
