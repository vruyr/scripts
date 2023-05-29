#!/usr/bin/env python3

from argparse import Namespace
from os import name
import sys, urllib.parse, imaplib, ssl, getpass, hmac, email, shlex, subprocess, re, json
# pip install IMAPClient==2.2.0
from imapclient import imap_utf7

#TODO (encode|decode|b["']) - fix all the binary to text conversions, remove all hard-coded encodings.
verbosity=None


def main(opts):
	global verbosity
	verbosity = opts.verbosity

	url = urllib.parse.urlsplit(opts.account)
	assert url.scheme == "imaps", (opts.account, url)
	assert not url.fragment,      (opts.account, url)
	username, password, hostname, port = (url.username, url.password, url.hostname, url.port)
	username = urllib.parse.unquote(username)
	url_qs = urllib.parse.parse_qs(url.query)
	url_qs_ssl = url_qs.pop("ssl", None)
	assert not url_qs, url_qs

	port     = port or imaplib.IMAP4_SSL_PORT
	server   = opts.server   or hostname or input("Server Hostname: ")
	username = opts.username or username or input("Username: ") or getpass.getuser()
	password = opts.password or password or get_password(server, username)
	path     = opts.path     or url.path or ""

	ssl_context = ssl.create_default_context()
	if url_qs_ssl is None:
		pass
	elif url_qs_ssl == ["promiscuous"]:
		ssl_context.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
		ssl_context.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
		ssl_context.set_ciphers("ALL:@SECLEVEL=0")
		ssl_context.check_hostname = False
		ssl_context.verify_mode = ssl.CERT_NONE
	else:
		assert False, ("Unrecognized ssl query parameter value", url_qs_ssl)

	conn = imaplib.IMAP4_SSL(server, port=port, ssl_context=ssl_context)

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

	personal_ns, otherusers_ns, shared_ns = get_namespaces(conn)
	assert len(personal_ns) == 1, personal_ns
	personal_ns = personal_ns[0]
	assert len(personal_ns) == 2, personal_ns
	personal_ns_prefix, personal_ns_delimiter = personal_ns
	assert personal_ns_prefix == "", (personal_ns_prefix,)

	path_sep = "/"
	path = path.strip(path_sep)
	path = [urllib.parse.unquote(i) for i in path.split(path_sep)] if path else []

	if path:
		mailbox = personal_ns_delimiter.join(path)
		#TODO:vruyr:bugs Special chars, such as hierarchy delimiter, in path components should be escaped.
		list_mailbox_content(conn=conn, mailbox=mailbox)
	else:
		list_mailboxes(conn=conn, show_in_json=opts.show_in_json)


def get_namespaces(conn: imaplib.IMAP4):
	response_type, response_data = conn.namespace()
	assert response_type == "OK"
	assert type(response_data) == list and len(response_data) == 1
	namespace_response = response_data[0].decode("ASCII")

	# https://www.atmail.com/blog/imap-101-manual-imap-sessions/
	# https://datatracker.ietf.org/doc/html/rfc2342.html

	namespaces = []
	i = 0
	size = len(namespace_response)
	prefix_and_delimiter_p = re.compile(r'"([^"]*)" "([^"]*)"')
	while i < size:
		if namespace_response[i] == " ":
			i += 1
			continue

		if namespace_response[i:i+3] == "NIL":
			namespaces.append(None)
			i += 3
			continue

		if namespace_response[i] == "(":
			i += 1
			prefixes_and_delimiters = []
			while namespace_response[i] == "(":
				j = namespace_response.find(")", i + 1)
				assert j >= 0, (i, j, namespace_response)
				prefix_and_delimiter = namespace_response[i+1:j]
				try:
					prefix, delimiter = prefix_and_delimiter_p.fullmatch(prefix_and_delimiter).groups()
					prefixes_and_delimiters.append((prefix, delimiter))
				except:
					print(prefix_and_delimiter)
				i = j+1
			assert namespace_response[i] == ")", (i, namespace_response)
			i += 1
			namespaces.append(tuple(prefixes_and_delimiters))
			continue

		assert False, (i, namespace_response[i:], namespace_response)

	personal_ns, otherusers_ns, shared_ns = namespaces

	return personal_ns, otherusers_ns, shared_ns


def list_mailbox_content(*, conn: imaplib.IMAP4, mailbox):
		mailbox = imap_utf7_encode(mailbox)
		mailbox = b'"' + mailbox + b'"' #TODO Why do we need to quotes here and what happens if the name already has a quote.
		response_type, response_data = conn.select(mailbox, readonly=True)
		if response_type != "OK":
			show_msg(-1, "{!r}, {!r}", response_type, response_data)
			return

		response_type, response_data = conn.search(None, "ALL")
		assert response_type == "OK"
		assert len(response_data) == 1
		if response_data == [None]:
			print("(empty)")
			return
		msgns = response_data[0].split()
		for msgn in msgns:
			msg_part = b"RFC822.HEADER"
			response_type, response_data = conn.fetch(msgn, b"(" + msg_part + b")")
			assert response_type == "OK"
			(envelope_start, message_data), envelope_end = response_data
			expected_envelope_start = b"%b (%s {%d}"% (msgn, msg_part, len(message_data))
			assert envelope_start == expected_envelope_start
			assert envelope_end == b")"
			msg = email.message_from_bytes(message_data)
			print(
				"{n}\tDate: {d}\tFrom: {f}\tTo: {t}\tSubject: {s!r}\tMessage-ID: {i}".format(
					n=msgn.decode("ASCII"),
					d=msg["Date"],
					f=msg["From"],
					t=msg["To"],
					s=msg["Subject"],
					i=msg["Message-ID"],
				),
				end="\n"
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
	connectivity.add_argument("--account", "-a",  dest="account",  action="store", metavar="IMAP_URL", help="IMAP account to connect to as an imap://user@hostname/mailbox/path url")
	connectivity.add_argument("--server", "-s",   dest="server",   action="store",               metavar="HOST",     help="host name or IP address of the IMAP server")
	connectivity.add_argument("--user", "-u",     dest="username", action="store", default=None, metavar="USERNAME", help="default is {}".format(getpass.getuser()))
	connectivity.add_argument("--password",       dest="password", action="store",               metavar="PASSWORD")
	connectivity.add_argument("--path", "-p",     dest="path",     action="store",               metavar="MAILBOX_PATH")

	opts = parser.parse_args()
	opts.verbosity -= opts._negative_verbosity
	del opts._negative_verbosity
	return main(opts)


if __name__ == '__main__':
	sys.exit(sysmain())
