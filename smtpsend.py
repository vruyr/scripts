#!/usr/bin/env python3

from __future__ import print_function
import sys; assert sys.version_info[:2] in [(3, 5), (3, 6)]
import argparse, logging, email.mime.text, getpass, socket, smtplib


# TODO change --smtp parameter to --server and start using `secret` just like imap.py does


lgr = logging.getLogger(__name__)


def main(argv=None):
	opts = _parse_args(argv)
	_configure_logging(debug=opts.debug)

	username = None
	password = None
	if opts.username is not None:
		username = opts.username
		password = getpass.getpass(prompt=("Password for %s: " % username))

	msg = email.mime.text.MIMEText(load_text(opts.file))

	if opts.msg_subject is not None:
		msg["Subject"] = opts.msg_subject
	if opts.msg_from is not None:
		msg["From"] = opts.msg_from
	else:
		msg["From"] = "%s@%s" % (getpass.getuser(), socket.gethostname())
	if opts.msg_to is not None:
		msg["To"] = ", ".join(opts.msg_to)
	if opts.msg_cc is not None:
		msg["CC"] = ", ".join(opts.msg_cc)
	if opts.msg_bcc is not None:
		msg["BCC"] = ", ".join(opts.msg_bcc)

	if not opts.silent:
		print(msg)
		if opts.debug:
			print("-" * 40)

	with smtplib.SMTP() as s:
		if opts.debug:
			s.set_debuglevel(2)
		s.connect(opts.smtp_server)
		if username is not None:
			s.login(username, password)
		s.send_message(msg)


def load_text(filename):
	if filename == "-":
		return sys.stdin.read()
	with open(filename) as fp:
		return fp.read()


def _configure_logging(*, debug=False):
	logging.basicConfig(level=(logging.DEBUG if debug else logging.INFO))


def _parse_args(argv):
	parser = argparse.ArgumentParser(prog=(argv[0] if argv is not None else None))
	parser.add_argument("--debug", action="store_true", default=False)
	parser.add_argument("--silent", action="store_true", default=False)
	parser.add_argument("--smtp", dest="smtp_server", action="store", default="localhost")
	parser.add_argument("--username", "-u", dest="username", action="store", default=None)
	parser.add_argument("--from", "-f", dest="msg_from", action="store", default=None)
	parser.add_argument("--to", "-t", dest="msg_to", action="append", default=None)
	parser.add_argument("--cc", "-c", dest="msg_cc", action="append", default=None)
	parser.add_argument("--bcc", "-b", dest="msg_bcc", action="append", default=None)
	parser.add_argument("--subject", "-s", dest="msg_subject", action="store", default=None)
	parser.add_argument("file", nargs=None, help="stdin if -")
	opts = parser.parse_args(argv[1:] if argv is not None else None)
	if (opts.msg_to, opts.msg_cc, opts.msg_bcc) == (None, None, None):
		parser.error("At least one of to, cc or bcc should be specified.")
	return opts

if __name__ == '__main__':
	sys.exit(main())
