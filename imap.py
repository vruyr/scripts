#!/usr/bin/env python3

import sys, urllib.parse, imaplib, getpass, hmac, email, shlex, subprocess, re, json
# pip install IMAPClient==2.2.0
from imapclient import imap_utf7

#TODO (encode|decode|b["']) - fix all the binary to text conversions, remove all hard-coded encodings.
verbosity=None


def main(opts):
	global verbosity
	verbosity = opts.verbosity

	url = urllib.parse.urlsplit(opts.account)
	assert url.scheme == "imap", (opts.account, url)
	assert not url.path,         (opts.account, url)
	assert not url.query,        (opts.account, url)
	assert not url.fragment,     (opts.account, url)
	username, password, hostname, port = (url.username, url.password, url.hostname, url.port)
	username = urllib.parse.unquote(username)
	port = port or imaplib.IMAP4_SSL_PORT

	server = opts.server or hostname or input("Server Hostname: ")
	username = opts.username or username or input("Username: ") or getpass.getuser()
	password = opts.password or password or get_password(server, username)

	conn = imaplib.IMAP4_SSL(server, port=port)
	show_msg(2, "Server Capabilities: {}", ", ".join(conn.capabilities))

	if "AUTH=CRAM-MD5" in conn.capabilities:
		if True:
			conn.login_cram_md5(username, password)
		else:
			def cram_responder(challenge):
				h1 = hmac.new(key=password.encode("ascii"), msg=challenge, digestmod="md5").hexdigest()
				h2 = username.strip() + " " + h1
				return h2.encode("ascii")
			conn.authenticate("CRAM-MD5", cram_responder)
	elif "AUTH=PLAIN" in conn.capabilities:
		if True:
			conn.login(username, password)
		else:
			#TODO AUTH=PLAIN doesn't work
			def plain_responder(challenge):
				show_msg(1, "Challenge: {!r}", challenge)
				return ("{0}\x00{0}\x00{1}".format("username", "password")).encode("ascii")
			conn.authenticate("PLAIN", plain_responder)
	else:
		show_msg(-1, "Error: No known authentication mechanisms are supported by the server.")
		return

	if opts.list_mailboxes:
		list_mailboxes(conn=conn, show_in_json=opts.show_in_json)
	elif opts.new_mailbox is not None:
		new_mailbox = imap_utf7_encode(opts.new_mailbox)
		new_mailbox = b'"' + new_mailbox + b'"' #TODO Why do we need to quotes here and what happens if the name already has a quote.
		conn.create(new_mailbox)
	else:
		if opts.mailbox is None:
			opts.mailbox = "INBOX"

	if opts.mailbox is not None:
		list_mailbox_content(conn=conn, mailbox=opts.mailbox)


def list_mailbox_content(*, conn, mailbox):
		mailbox = imap_utf7_encode(mailbox)
		mailbox = b'"' + mailbox + b'"' #TODO Why do we need to quotes here and what happens if the name already has a quote.
		response_type, response_data = conn.select(mailbox, readonly=True)
		if response_type != "OK":
			show_msg(-1, "{!r}, {!r}", response_type, response_data)
			return

		print()
		response_type, response_data = conn.search(None, "ALL")
		assert response_type == "OK"
		assert len(response_data) == 1
		msgns = response_data[0].split()
		for msgn in msgns:
			response_type, response_data = conn.fetch(msgn, "(RFC822)")
			assert response_type == "OK"
			(envelope_start, message_data), envelope_end = response_data
			expected_envelope_start = b"%b (RFC822 {%d}"% (msgn, len(message_data))
			assert envelope_start == expected_envelope_start
			assert envelope_end == b")"
			msg = email.message_from_bytes(message_data)
			print(
				"{n}\nFrom: {f}\nTo: {t}\nDate: {d}\nSubject: {s}\nMessage-ID: {i}".format(
					n=msgn.decode("ASCII"),
					f=msg["From"],
					t=msg["To"],
					d=msg["Subject"],
					s=msg["Date"],
					i=msg["Message-ID"],
				),
				end="\n\n"
			)


def list_mailboxes(*, conn, show_in_json):
	# https://www.imapwiki.org/ClientImplementation/MailboxList
	status, mailboxes = conn.list("\"\"", "*")
	assert status == "OK"
	if show_in_json:
		result = []
		for mailbox in mailboxes:
			tags, sep, path = parse_imap_list_response_entry(imap_utf7_decode(mailbox))
			result.append({
				"tags": list(tags),
				"path": list(p for p in path),
			})
		json.dump(result, sys.stdout, indent=4)
		sys.stdout.write("\n")
	else:
		for mailbox in mailboxes:
			tags, sep, path = parse_imap_list_response_entry(imap_utf7_decode(mailbox))
			print(" ".join(tags).ljust(12), sep.join(p for p in path))


def imap_utf7_encode(x):
	return imap_utf7.encode(x)


def imap_utf7_decode(x):
	return imap_utf7.decode(x)


def parse_imap_list_response_entry(entry):
	m = re.match(r"""^\(([^)]*)\)\s+"([^"])"\s+"?([^"]+)"?$""", entry)
	if m:
		tags, sep, path = m.groups()
		path = path.split(sep)
		tags = tags.split()
		for tag in ["\\HasNoChildren", "\\HasChildren"]:
			if tag not in tags:
				continue
			tags.remove(tag)
		return (tags, sep, path)
	else:
		return entry


def get_password(server, username):
	p = subprocess.run(
		["security", "find-internet-password", "-r", "imap", "-s", server, "-a", username, "-w"],
		shell=False,
		stdin=subprocess.DEVNULL,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
	)
	if p.returncode == 0:
		password = p.stdout.decode().rstrip("\r\n")
		show_msg(2, "Found the password in Keychain.")
		return password
	show_msg(2, "No password found in Keychain, prompting.")
	password = getpass.getpass("Password ({u}@{s}): ".format(u=username, s=server))
	show_msg(0, "To save the password, execute: {}", " ".join(shlex.quote(x) for x in [
		"security", "add-internet-password",
		"-r", "imap",
		"-s", server,
		"-a", username,
		"-w"
	]))
	return password


def show_msg(verbosity_, msg, *args, **kwargs):
	global verbosity
	if verbosity_ > verbosity:
		return
	print(msg.format(*args, **kwargs))


def sysmain():
	import argparse
	parser = argparse.ArgumentParser()

	output_options = parser.add_argument_group("Output Options")
	output_options.add_argument("--json", "-j",    dest="show_in_json",        action="store_true", default=False)
	output_options.add_argument("--verbose", "-v", dest="verbosity",           action="count",      default=0, help="increase verbosity, can be used multiple times")
	output_options.add_argument("--quiet", "-q",   dest="_negative_verbosity", action="count",      default=0, help="decrease verbosity, can be used multiple times")


	connectivity = parser.add_argument_group("Connectivity")
	connectivity.add_argument("--account", "-a", dest="account", action="store", metavar="IMAP_URL", help="IMAP account to connect to as an imap:// url")
	connectivity.add_argument("--server", "-s",   dest="server",   action="store",               metavar="HOST",     help="host name or IP address of the IMAP server")
	connectivity.add_argument("--user", "-u",     dest="username", action="store", default=None, metavar="USERNAME", help="default is {}".format(getpass.getuser()))
	connectivity.add_argument("--password", "-p", dest="password", action="store",               metavar="PASSWORD")

	actions = parser.add_argument_group("Actions")
	actions.add_argument("--mailbox", "-m",        dest="mailbox",        action="store", metavar="MAILBOX", default=None)
	actions.add_argument("--new-mailbox", "-n",    dest="new_mailbox",    action="store", metavar="MAILBOX", default=None)
	actions.add_argument("--list-mailboxes", "-l", dest="list_mailboxes", action="store_true",               default=False)

	opts = parser.parse_args()
	opts.verbosity -= opts._negative_verbosity
	del opts._negative_verbosity
	return main(opts)


if __name__ == '__main__':
	sys.exit(sysmain())
