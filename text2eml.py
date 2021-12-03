#!/usr/bin/env python3.9

"""
Usage:
	{prog} [options] --from=ADDR --to=ADDR --subject=TEXT [--] [<cmd> [<cmd_args>...]]


Options:
	--from, -f ADDR       The "From" MIME header value.
	--to, -t ADDR         The "To" MIME header value.
	--subject, -s TEXT    The "Subject" MIME header value.
	--font-size, -x SIZE  The font size to use in the resulting message.
"""

import sys, locale, os, xml.dom.minidom, email.message, subprocess
# pip install docopt==0.6.2
import docopt


CHAR_NBSP="\u00A0" # No-Break Space


def main(*, args, prog):
	locale.setlocale(locale.LC_ALL, "")

	params = docopt.docopt(
		__doc__.replace("\t", " " * 4).format(prog=os.path.basename(prog)),
		argv=args,
		help=True,
		version=True,
		options_first=False
	)
	msg_from = params.pop("--from")
	msg_to = params.pop("--to")
	msg_subject = params.pop("--subject")
	font_size = params.pop("--font-size")
	params.pop("--")
	cmd = params.pop("<cmd>")
	cmd_args = params.pop("<cmd_args>")
	assert not params, params

	data = sys.stdin.read()

	if not data:
		return 0


	impl = xml.dom.minidom.getDOMImplementation()
	doc = impl.createDocument(
		"http://www.w3.org/1999/xhtml",
		"html",
		impl.createDocumentType(
			"html",
			"-//W3C//DTD XHTML 1.0 Strict//EN",
			"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd",
		),
	)
	html = doc.documentElement
	html.appendChild(head := doc.createElement("head"))
	head.appendChild(meta := doc.createElement("meta"))
	meta.setAttribute("name", "viewport")
	meta.setAttribute("content", "width=device-width, initial-scale=1, minimum-scale=1")
	head.appendChild(style := doc.createElement("style"))
	style.appendChild(doc.createTextNode(f"""
		.text {{
			white-space: nowrap;
			font-family: monospace;
			{"font-size: " + font_size + ";" if font_size else ""}
		}}

		.line {{
		}}
	"""))
	html.appendChild(body := doc.createElement("body"))
	body.appendChild(text_container := doc.createElement("div"))
	text_container.setAttribute("class", "text")
	for line in data.splitlines():
		line = line.replace(" ", CHAR_NBSP) if line else CHAR_NBSP
		text_container.appendChild(line_container := doc.createElement("div"))
		line_container.appendChild(doc.createTextNode(line))
		line_container.setAttribute("class", "line")

	encoding = "UTF-8"

	msg = email.message.EmailMessage()
	msg.set_content(
		doc.toprettyxml(encoding=encoding, standalone=True).decode(encoding),
		subtype="html", charset=encoding, cte="quoted-printable",
	)

	msg["From"] = msg_from
	msg["To"] = msg_to
	msg["Subject"] = msg_subject

	result = msg.as_bytes(unixfrom=False)

	if cmd is None:
		sys.stdout.buffer.write(result)
	else:
		subprocess.run(
			[cmd, *cmd_args], input=result,
			capture_output=False, shell=False, timeout=None, check=True, text=False,
		)


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
