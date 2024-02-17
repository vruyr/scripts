#!/usr/bin/swift

import Foundation

let now = Date()
let formatter = DateFormatter()
formatter.locale = Locale(identifier: "en_US")
// https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/DataFormatting/Articles/dfDateFormatting10_4.html
// https://www.unicode.org/reports/tr35/tr35-31/tr35-dates.html#Date_Format_Patterns
formatter.dateFormat = "YY'W'ww"
print(formatter.string(from: now))
