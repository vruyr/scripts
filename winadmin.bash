_winadmin_promptmessage=
function winadmin_check() {
	py -c '
		import sys, ctypes
		sys.exit(0 if ctypes.windll.shell32.IsUserAnAdmin() else 1)
	' && {
		_promptmessage_add '!!!ADMIN!!!'
		_winadmin_promptmessage=${promptmessage_added_index}
	} || {
		test -n "${_winadmin_promptmessage}" _promptmessage_remove ${_winadmin_promptmessage}
		_winadmin_promptmessage=
	}
}
