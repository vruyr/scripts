#!/usr/bin/env swift

import func Darwin.exit
import func Darwin.getpid
import func Darwin.proc_pidpath
import func Darwin.sysctl
import var Darwin.CTL_KERN
import var Darwin.KERN_PROC
import var Darwin.KERN_PROC_PID
import var Darwin.MAXPATHLEN
import struct Darwin.kinfo_proc
import typealias Darwin.pid_t
import typealias Darwin.u_int
import class AppKit.NSRunningApplication

extension pid_t {
    /// Returns the parent pid, or nil on error or if at root.
    var parent: pid_t? {
        var proc = kinfo_proc()
        var size = MemoryLayout<kinfo_proc>.stride
        // MIB path to kern.proc.pid.<pid>
        var mib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, self]
        guard sysctl(&mib, u_int(mib.count), &proc, &size, nil, 0) == 0 else { return nil }
        let ppid = proc.kp_eproc.e_ppid
        return ppid > 0 ? ppid : nil
    }

    /// Returns the executable path for this pid, or nil if unavailable.
    var execPath: String? {
        var buf = [CChar](repeating: 0, count: Int(MAXPATHLEN))
        let ret = proc_pidpath(self, &buf, UInt32(buf.count))
        guard ret > 0 else { return nil }
        return String(cString: buf)
    }

    /// Returns an NSRunningApplication for GUI-launched apps, or nil if the PID has no associated GUI application.
    var app: NSRunningApplication? {
        NSRunningApplication(processIdentifier: self)
    }
}

// https://developer.apple.com/documentation/swift/sequence%28first%3Anext%3A%29
let frontmostApp = sequence(first: getpid(), next: { $0.parent })
    .first(where: { $0.app != nil })
    .flatMap { $0.app }

if let frontmostApp = frontmostApp {
    frontmostApp.activate(options: [])
} else {
	exit(1)
}
