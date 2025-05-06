#!/usr/bin/env swift

import Foundation
import AppKit

func main() {
	let pasteboard = NSPasteboard.general
	let args = CommandLine.arguments

	let requestedType: NSPasteboard.PasteboardType? = args.count > 1 ? NSPasteboard.PasteboardType(args[1]) : nil

	if let type = requestedType {
		printFullContent(pasteboard, of: type)
	} else {
		for (index, type) in (pasteboard.types ?? []).enumerated() {
			print("\(index + 1). \(type.rawValue)")

			if let data = pasteboard.data(forType: type) {
				print("    🔹 Data size: \(data.count) bytes")

				if let string = String(data: data, encoding: .utf8) {
					let preview = string.prefix(50).replacingOccurrences(of: "\n", with: "\\n")
					print("    🔹 UTF-8 String preview: \"\(preview)\"")
				} else {
					print("    🔹 (Non-text binary data)")
				}
			} else {
				print("    ⚠️ No data found for this type.")
			}
			print()
		}
	}
}


func printFullContent(_ pasteboard: NSPasteboard, of type: NSPasteboard.PasteboardType) {
	guard let data = pasteboard.data(forType: type) else {
		return
	}

	// Try UTF-8 decoding
	if let string = String(data: data, encoding: .utf8) {
		print(string)
	} else {
		// Fall back to raw hex dump
		let hex = data.map { String(format: "%02hhx", $0) }.joined(separator: " ")
		print(hex)
	}
}

main()
