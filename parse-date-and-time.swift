#!/usr/bin/env swift

// tools: Opus 4.7 Adaptive via Claude.ai via Safari via macOS
// disclaimers: AI-generated


// Compile: swiftc -O parse-date-and-time.swift -o parse-date-and-time

import Foundation

let input = CommandLine.arguments.count > 1
    ? CommandLine.arguments[1]
    : String(data: FileHandle.standardInput.readDataToEndOfFile(), encoding: .utf8) ?? ""

let detector = try NSDataDetector(types: NSTextCheckingResult.CheckingType.date.rawValue)
let fullRange = NSRange(input.startIndex..., in: input)

guard let match = detector.matches(in: input, range: fullRange).first,
      let date = match.date,
      let matchedRange = Range(match.range, in: input) else {
    FileHandle.standardError.write("no date found\n".data(using: .utf8)!)
    exit(1)
}

// Inspect the substring NSDataDetector actually matched for time tokens.
let matched = String(input[matchedRange])
let timeRegex = try NSRegularExpression(
    pattern: #"(?i)\d{1,2}:\d{2}|\b\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.)\b|\b(?:noon|midnight|midday)\b|\bo'?clock\b|T\d{2}"#
)
let hasTime = timeRegex.firstMatch(
    in: matched,
    range: NSRange(matched.startIndex..., in: matched)
) != nil

let fmt = ISO8601DateFormatter()
fmt.timeZone = .current
fmt.formatOptions = hasTime ? [.withInternetDateTime] : [.withFullDate]
print(fmt.string(from: date))
