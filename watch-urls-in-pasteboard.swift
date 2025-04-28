#!/usr/bin/swift

import Foundation
import AppKit


func main() async {
	signal(SIGINT) { signal in
		print("\nBye...")
		exit(0)
	}

	signal(SIGWINCH) { signal in
		print("\nTerminal Size Changed")
	}

	let pasteboard = NSPasteboard.general
	var lastChangeCount = pasteboard.changeCount

	print("Watching pasteboard for valid URLs...")

	while true {
		do {
			try await Task.sleep(nanoseconds: 100_000_000)
		} catch {
			print("Error during sleep or task: \(error)")
			break
		}

		if pasteboard.changeCount == lastChangeCount { continue }

		lastChangeCount = pasteboard.changeCount
		let outputPrefix = "[\(lastChangeCount)] "

		guard let pasteboardContent = pasteboard.string(forType: .string) else {
			print("Pasteboard content is nil.")
			continue
		}

		if !isValidURL(pasteboardContent) {
			print("\(outputPrefix)Not a valid URL.")
			continue
		}

		Task {
			print("\(outputPrefix)\(pasteboardContent)")
			do {
				let exitCode = try await runCommand(
					"/Users/vruyr/.bin/python/venv/getpocket-cpython-3.10.0/bin/yt-dlp",
					arguments: [
						"--simulate",
						pasteboardContent
					],
					prefix: "\(outputPrefix)"
				)
				print("\(outputPrefix)Exit Code: \(exitCode)")
			} catch {
				print("\(outputPrefix)Failed to run command: \(error)")
			}
		}
	}
}


func isValidURL(_ text: String) -> Bool {
	guard let url = URL(string: text), url.scheme != nil, url.host != nil else {
		return false
	}
	return true
}


func runCommand(_ command: String, arguments: [String], prefix: String) async throws -> Int32 {
	let process = Process()
	process.executableURL = URL(fileURLWithPath: command)
	process.arguments = arguments

	let pipe = Pipe()
	process.standardOutput = pipe

	let fileHandle = pipe.fileHandleForReading

	try process.run()

	do {
		let numLinesToKeep: Int32 = 5
		var outputLines: [String] = []
		for try await addedLine in fileHandle.bytes.lines {
			outputLines.append(addedLine)
			var printFrom = outputLines.count - 1
			if outputLines.count > numLinesToKeep {
				outputLines.removeFirst()
				print("\u{001B}[\(numLinesToKeep)F\u{001B}[0J", terminator: "")
				printFrom = 0
			}
			for line in outputLines[printFrom...] {
				print("\(prefix)\(line)")
			}
		}
	} catch {
		throw error
	}

	await withCheckedContinuation { continuation in
		process.terminationHandler = { _ in
			continuation.resume()
		}
	}

	return process.terminationStatus
}


await main()
