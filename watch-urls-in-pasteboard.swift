#!/usr/bin/swift

import Foundation
import AppKit


struct CliOptions {
	var commandToExec: [String]
	var numLinesToShow: UInt = 5
}


func main(options: CliOptions) async {
	signal(SIGINT) { signal in
		print("\nBye...")
		exit(0)
	}

	signal(SIGWINCH) { signal in
		print("\nTerminal Size Changed")
	}

	let commandToExecCmd: URL = resolveCommand(options.commandToExec.first!)
	print("Resolved command path: \(commandToExecCmd.path)")

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

		let commandToExecArgs: [String] = options.commandToExec.dropFirst().map {
			$0 == "{}" ? pasteboardContent : $0
		}

		Task {
			print("\(outputPrefix)\(pasteboardContent)")
			do {
				let exitCode = try await runCommand(
					commandToExecCmd,
					arguments: commandToExecArgs,
					prefix: "\(outputPrefix)",
					numLinesToShow: options.numLinesToShow
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

func isExecutableFile(atPath path: String) -> Bool {
	var isDirectory: ObjCBool = false
	let exists = FileManager.default.fileExists(atPath: path, isDirectory: &isDirectory)
	return (
		exists
		&& !isDirectory.boolValue
		&& FileManager.default.isExecutableFile(atPath: path)
	)
}

func resolveCommand(_ command: String) -> URL {
	// If already an absolute or relative path, use as is.
	if command.contains("/"){
		let fileURL = URL(fileURLWithPath: command)
		if !isExecutableFile(atPath: fileURL.path) {
			print("ERROR: The path \(String(reflecting: command)) is not executable file.")
			exit(2)
		}
		return fileURL
	}

	// Otherwise, search in PATH

	let envPath = ProcessInfo.processInfo.environment["PATH"] ?? ""
	for dir in envPath.split(separator: ":") {
		let candidate = URL(fileURLWithPath: String(dir)).appendingPathComponent(command)
		if FileManager.default.isExecutableFile(atPath: candidate.path) {
			return candidate
		}
	}

	print("ERROR: An executable \(String(reflecting: command)) was not found in PATH.")
	exit(3)
}


func runCommand(_ command: URL, arguments: [String], prefix: String, numLinesToShow: UInt) async throws -> Int32 {
	let process = Process()
	process.executableURL = command
	process.arguments = arguments

	let pipe = Pipe()
	process.standardOutput = pipe

	let fileHandle = pipe.fileHandleForReading

	try process.run()

	do {
		var outputLines: [String] = []
		for try await addedLine in fileHandle.bytes.lines {
			outputLines.append(addedLine)
			var printFrom = outputLines.count - 1
			if outputLines.count > numLinesToShow {
				outputLines.removeFirst()
				print("\u{001B}[\(numLinesToShow)F\u{001B}[0J", terminator: "")
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

func parseArguments(_ args: [String]) -> CliOptions {
	var options: CliOptions = CliOptions(commandToExec: [])

	var parsingOptions = true

	// First one is the script name, so we skip it
	for arg in args.dropFirst() {
		if !parsingOptions {
			options.commandToExec.append(arg)
			continue
		}

		if arg == "--" {
			parsingOptions = false
			continue
		}

		var key: String;
		var value: String;

		if arg.hasPrefix("-") && !arg.hasPrefix("--") {
			// Short option
			let option = String(arg.dropFirst())
			if option.count == 1 {
				key = option
				value = ""
			} else {
				key = String(option.prefix(1))
				value = String(option.dropFirst())
			}
		} else if arg.hasPrefix("--") && arg.contains("=") {
			// Long option with value
			let eqIdx = arg.firstIndex(of: "=")!
			key = String(arg.dropFirst(2).prefix(upTo: eqIdx))
			value = String(arg[arg.index(after: eqIdx)...])
		} else if arg.hasPrefix("--") && !arg.contains("=") {
			// Long option without value
			key = String(arg.dropFirst(2))
			value = ""
		} else {
			// Not an option. This must be first first arg that starts the command
			parsingOptions = false
			options.commandToExec.append(arg)
			continue
		}

		assert(!key.isEmpty, "Option key cannot be empty")

		if ["h", "help"].contains(key) {
			print("""
			Usage: watch-urls-in-pasteboard.swift [options] -- [command ...]

			Options:
			  -h, --help               Show this help message and exit
			  --lines-to-show=N, -l N  Number of lines to show in the output for each command.

			After the -- separator, you can specify an external command and its arguments.
			""")
			exit(0)
		} else if ["l", "--lines-to-show"].contains(key) {
			// Handle lines to show option
			if let numLinesToShow = UInt(value) {
				options.numLinesToShow = numLinesToShow
			} else {
				print("Invalid value for --lines-to-show: \(value)")
				exit(1)
			}
		} else {
			print("Unknown option: \(key)")
			exit(1)
		}
	}

	return options
}


await main(options: parseArguments(CommandLine.arguments))
