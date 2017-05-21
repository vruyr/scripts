#!/usr/bin/env python3

import sys
assert sys.version_info[:2] in [(3, 6)]
import imaplib, getpass, hmac, email


#TODO (encode|decode|b["']) - fix all the binary to text conversions, remove all hard-coded encodings.


def main(opts):
	server  = opts.server or input("Server: ")
	username = opts.username or input("Username: ") or getpass.getuser()
	password = opts.password or getpass.getpass("Password ({u}@{s}): ".format(u=username, s=server))

	conn = imaplib.IMAP4_SSL(server)
	print("Server Capabilities:", ", ".join(conn.capabilities))

	if "AUTH=CRAM-MD5" in conn.capabilities:
		if True:
			conn.login_cram_md5(username, password)
		else:
			def cram_responder(challenge):
				h1 = hmac.new(key=password.encode("ascii"), msg=challenge, digestmod="md5").hexdigest()
				h2 = username.strip() + " " + h1
				return h2.encode("ascii")
			conn.authenticate("CRAM-MD5", cram_responder)
	elif "AUTH=PLAIN  DOESNT-WORK" in conn.capabilities:
		def plain_responder(challenge):
			print("Challenge:", challenge)
			return ("{0}\x00{0}\x00{1}".format("username","password")).encode("ascii")
		conn.authenticate("PLAIN", plain_responder)
	else:
		print("Error: No supported authentication mechanisms are supported by the server.")
		return

	if opts.list_mailboxes:
		status, mailboxes = conn.list()
		assert status == "OK"
		for mailbox in mailboxes:
			mailbox = mailbox.decode("ASCII")
			print(mailbox)

	response_type, response_data = conn.select(opts.mailbox, readonly=True)
	if response_type != "OK":
		print(response_type, response_data)
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
		rfc822msg = message_data.decode("UTF-8")
		msg = email.message_from_string(rfc822msg)
		print(
			"{n}\nFrom: {f}\nTo: {t}\nDate: {d}\nSubject: {s}".format(
				n=msgn.decode("UTF-8"),
				f=msg["from"],
				t=msg["to"],
				d=msg["subject"],
				s=msg["date"],
			),
			end="\n\n"
		)


def sysmain():
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--server", "-s",
		dest="server",
		action="store",
		metavar="HOST",
		help="host name or IP address of the IMAP server"
	)
	parser.add_argument(
		"--user", "-u",
		dest="username",
		action="store",
		default=None,
		metavar="USERNAME",
		help="default is {}".format(getpass.getuser())
	)
	parser.add_argument(
		"--password", "-p",
		dest="password",
		action="store",
		metavar="PASSWORD"
	)
	parser.add_argument(
		"--mailbox", "-m",
		dest="mailbox",
		action="store",
		metavar="MAILBOX",
		default="INBOX",
		help="default is INBOX"
	)
	parser.add_argument(
		"--list-mailboxes", "-l",
		dest="list_mailboxes",
		action="store_true",
		default=False,
	)
	opts = parser.parse_args()
	return main(opts)


if __name__ == '__main__':
	sys.exit(sysmain())
