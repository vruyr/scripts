#!/usr/bin/env python
# vim:noexpandtab:

import sys, os, subprocess, select, fcntl, errno, datetime

def main():
	start = datetime.datetime.now()
	outfd = sys.stdout.fileno()

	(stdout_r, stdout_w) = os.pipe()
	(stderr_r, stderr_w) = os.pipe()

	fcntl.fcntl(stdout_r, fcntl.F_SETFL, os.O_NONBLOCK)
	fcntl.fcntl(stderr_r, fcntl.F_SETFL, os.O_NONBLOCK)

	p = subprocess.Popen(sys.argv[1:], stdout=stdout_w, stderr=stderr_w)

	fdlabel = { stdout_r: 'OUT: ', stderr_r: 'ERR: ' }
	fddata = { stdout_r: "", stderr_r: "" }

	while True:
		try:
			(r, w, x) = select.select([stdout_r, stderr_r], [], [], 0.1)
			for fd in r:
				d = os.read(fd, 10*1024*1024)
				if '\n' not in d:
					fddata[fd] += d
					continue
				else:
					d = fddata[fd] + d
					fddata[fd] = ""
				os.write(outfd, ''.join([fdlabel[fd] + l for l in d.splitlines(True)]))
		except OSError, e:
			if e.errno == errno.EAGAIN:
				continue
			else:
				raise

		if p.poll() != None:
			break

	os.write(outfd, "Duration: " + str(datetime.datetime.now() - start) + "\n")

	return p.wait()


if __name__ == "__main__":
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		pass
