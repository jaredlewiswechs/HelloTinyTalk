import Foundation

// MARK: - Token Types for Syntax Highlighting

enum TTTokenKind {
    case keyword        // let, const, fn, return, if, else, for, while, etc.
    case keywordClassic // when, fin, blueprint, law, field, forge, reply, do, end, self
    case stepChain      // _filter, _sort, _map, _take, etc.
    case operatorKw     // and, or, not, is, isnt, has, hasnt, isin, islike
    case typeKw         // int, float, str, bool, list, map, any, void
    case builtin        // show, print, len, range, etc.
    case constant       // true, false, null, nil, PI, E, TAU, INF
    case identifier
    case number
    case string
    case stringEscape
    case stringInterp   // { } inside strings
    case comment
    case operatorSym    // + - * / = < > etc.
    case pipe           // |> %>%
    case bracket        // { } [ ] ( )
    case delimiter      // , . : ;
    case whitespace
    case newline
    case unknown
}

struct TTToken {
    let kind: TTTokenKind
    let range: NSRange
    let text: String
}

// MARK: - Lexer for Syntax Highlighting

class TinyTalkLexer {

    static let keywords: Set<String> = [
        "let", "const", "fn", "return", "if", "else", "elif",
        "for", "while", "in", "break", "continue", "match",
        "struct", "enum", "import", "from", "use", "as",
        "try", "catch", "throw",
    ]

    static let classicKeywords: Set<String> = [
        "when", "fin", "blueprint", "law", "field", "forge",
        "reply", "do", "end", "self",
    ]

    static let operatorKeywords: Set<String> = [
        "and", "or", "not", "is", "isnt", "has", "hasnt", "isin", "islike",
    ]

    static let typeKeywords: Set<String> = [
        "int", "float", "str", "string", "bool", "boolean",
        "list", "map", "any", "void", "null", "num", "number",
    ]

    static let builtins: Set<String> = [
        "show", "print", "len", "range", "abs", "round", "floor", "ceil",
        "sqrt", "pow", "min", "max", "sum", "sin", "cos", "tan", "log", "exp",
        "append", "push", "pop", "sort", "reverse", "contains", "slice",
        "keys", "values", "zip", "enumerate",
        "split", "join", "replace", "trim", "upcase", "downcase",
        "startswith", "endswith",
        "type", "assert", "assert_equal", "assert_true", "assert_false",
        "read_csv", "write_csv", "read_json", "write_json",
        "parse_json", "to_json", "http_get", "http_post",
        "date_now", "date_parse", "date_format", "date_floor",
        "date_add", "date_diff",
        "regex_match", "regex_find", "regex_replace", "regex_split",
        "file_read", "file_write", "file_exists", "file_list",
        "env", "args", "format", "hash", "md5", "sha256",
        "DataFrame",
        "chart_bar", "chart_line", "chart_pie", "chart_scatter",
        "chart_histogram", "chart_multi",
    ]

    static let constants: Set<String> = [
        "true", "false", "null", "nil", "PI", "E", "TAU", "INF",
    ]

    static let stepChains: Set<String> = [
        "_filter", "_sort", "_map", "_take", "_drop", "_first", "_last",
        "_reverse", "_unique", "_count", "_sum", "_avg", "_min", "_max",
        "_group", "_flatten", "_zip", "_chunk", "_reduce", "_sortBy",
        "_join", "_mapValues", "_each", "_select", "_mutate", "_summarize",
        "_summarise", "_rename", "_arrange", "_distinct", "_slice", "_pull",
        "_groupBy", "_group_by", "_leftJoin", "_left_join",
        "_pivot", "_unpivot", "_window",
    ]

    private let source: String
    private let chars: [Character]
    private var pos: Int = 0
    private var tokens: [TTToken] = []

    init(source: String) {
        self.source = source
        self.chars = Array(source)
    }

    func tokenize() -> [TTToken] {
        var result: [TTToken] = []
        var pos = 0
        let chars = self.chars
        let count = chars.count

        while pos < count {
            let startPos = pos
            let ch = chars[pos]

            // Newlines
            if ch == "\n" {
                pos += 1
                result.append(token(.newline, start: startPos, end: pos))
                continue
            }

            // Whitespace
            if ch == " " || ch == "\t" || ch == "\r" {
                pos += 1
                while pos < count && (chars[pos] == " " || chars[pos] == "\t" || chars[pos] == "\r") {
                    pos += 1
                }
                result.append(token(.whitespace, start: startPos, end: pos))
                continue
            }

            // Line comments: // or #
            if ch == "/" && pos + 1 < count && chars[pos + 1] == "/" {
                pos += 2
                while pos < count && chars[pos] != "\n" {
                    pos += 1
                }
                result.append(token(.comment, start: startPos, end: pos))
                continue
            }
            if ch == "#" {
                pos += 1
                while pos < count && chars[pos] != "\n" {
                    pos += 1
                }
                result.append(token(.comment, start: startPos, end: pos))
                continue
            }

            // Block comments: /* ... */
            if ch == "/" && pos + 1 < count && chars[pos + 1] == "*" {
                pos += 2
                while pos + 1 < count {
                    if chars[pos] == "*" && chars[pos + 1] == "/" {
                        pos += 2
                        break
                    }
                    pos += 1
                }
                if pos >= count { pos = count }
                result.append(token(.comment, start: startPos, end: pos))
                continue
            }

            // Strings
            if ch == "\"" || ch == "'" {
                let tokens = scanString(from: &pos, quote: ch)
                result.append(contentsOf: tokens)
                continue
            }

            // Numbers
            if ch.isNumber || (ch == "." && pos + 1 < count && chars[pos + 1].isNumber) {
                pos += 1
                // Hex/octal/binary
                if ch == "0" && pos < count {
                    let next = chars[pos]
                    if next == "x" || next == "X" {
                        pos += 1
                        while pos < count && (chars[pos].isHexDigit || chars[pos] == "_") { pos += 1 }
                        result.append(token(.number, start: startPos, end: pos))
                        continue
                    }
                    if next == "o" || next == "O" {
                        pos += 1
                        while pos < count && (chars[pos] >= "0" && chars[pos] <= "7" || chars[pos] == "_") { pos += 1 }
                        result.append(token(.number, start: startPos, end: pos))
                        continue
                    }
                    if next == "b" || next == "B" {
                        pos += 1
                        while pos < count && (chars[pos] == "0" || chars[pos] == "1" || chars[pos] == "_") { pos += 1 }
                        result.append(token(.number, start: startPos, end: pos))
                        continue
                    }
                }
                while pos < count && (chars[pos].isNumber || chars[pos] == "_") { pos += 1 }
                if pos < count && chars[pos] == "." && pos + 1 < count && chars[pos + 1].isNumber {
                    pos += 1
                    while pos < count && (chars[pos].isNumber || chars[pos] == "_") { pos += 1 }
                }
                if pos < count && (chars[pos] == "e" || chars[pos] == "E") {
                    pos += 1
                    if pos < count && (chars[pos] == "+" || chars[pos] == "-") { pos += 1 }
                    while pos < count && chars[pos].isNumber { pos += 1 }
                }
                result.append(token(.number, start: startPos, end: pos))
                continue
            }

            // Identifiers, keywords, step chains
            if ch.isLetter || ch == "_" {
                pos += 1
                while pos < count && (chars[pos].isLetter || chars[pos].isNumber || chars[pos] == "_") {
                    pos += 1
                }
                let text = String(chars[startPos..<pos])
                let kind = classifyWord(text)
                result.append(TTToken(kind: kind, range: NSRange(location: startPos, length: pos - startPos), text: text))
                continue
            }

            // Multi-char operators
            if pos + 2 < count {
                let three = String(chars[pos..<pos+3])
                if three == "%>%" {
                    pos += 3
                    result.append(token(.pipe, start: startPos, end: pos))
                    continue
                }
                if three == "..=" {
                    pos += 3
                    result.append(token(.operatorSym, start: startPos, end: pos))
                    continue
                }
            }
            if pos + 1 < count {
                let two = String(chars[pos..<pos+2])
                if two == "|>" {
                    pos += 2
                    result.append(token(.pipe, start: startPos, end: pos))
                    continue
                }
                let twoCharOps: Set<String> = [
                    "**", ":=", "==", "!=", "~~", "<=", ">=",
                    "&&", "||", "<<", ">>", "+=", "-=", "*=",
                    "/=", "%=", "->", "=>", "::", "..",
                ]
                if twoCharOps.contains(two) {
                    pos += 2
                    result.append(token(.operatorSym, start: startPos, end: pos))
                    continue
                }
            }

            // Brackets
            if "{}[]()".contains(ch) {
                pos += 1
                result.append(token(.bracket, start: startPos, end: pos))
                continue
            }

            // Delimiters
            if ",.:;?".contains(ch) {
                pos += 1
                result.append(token(.delimiter, start: startPos, end: pos))
                continue
            }

            // Single-char operators
            if "+-*/%<>=!&|^~@".contains(ch) {
                pos += 1
                result.append(token(.operatorSym, start: startPos, end: pos))
                continue
            }

            // Unknown
            pos += 1
            result.append(token(.unknown, start: startPos, end: pos))
        }

        return result
    }

    private func scanString(from pos: inout Int, quote: Character) -> [TTToken] {
        var tokens: [TTToken] = []
        let startPos = pos
        pos += 1  // skip opening quote

        // Check for triple-quote
        let isTriple = pos + 1 < chars.count && chars[pos] == quote && chars[pos + 1] == quote
        if isTriple {
            pos += 2
        }

        var segStart = startPos

        while pos < chars.count {
            let ch = chars[pos]

            // End of string
            if isTriple {
                if ch == quote && pos + 2 < chars.count && chars[pos + 1] == quote && chars[pos + 2] == quote {
                    pos += 3
                    tokens.append(token(.string, start: segStart, end: pos))
                    return tokens
                }
            } else {
                if ch == quote {
                    pos += 1
                    tokens.append(token(.string, start: segStart, end: pos))
                    return tokens
                }
                if ch == "\n" {
                    // Unterminated string
                    tokens.append(token(.string, start: segStart, end: pos))
                    return tokens
                }
            }

            // Interpolation in double-quoted strings
            if quote == "\"" && ch == "{" {
                // String part before {
                if pos > segStart {
                    tokens.append(token(.string, start: segStart, end: pos))
                }
                tokens.append(token(.stringInterp, start: pos, end: pos + 1))
                pos += 1

                // Scan tokens inside { } until we find matching }
                var depth = 1
                let interpStart = pos
                while pos < chars.count && depth > 0 {
                    if chars[pos] == "{" { depth += 1 }
                    if chars[pos] == "}" { depth -= 1; if depth == 0 { break } }
                    pos += 1
                }

                // Re-lex the interpolation content
                if pos > interpStart {
                    let interpSource = String(chars[interpStart..<pos])
                    let subLexer = TinyTalkLexer(source: interpSource)
                    let subTokens = subLexer.tokenize()
                    for st in subTokens {
                        tokens.append(TTToken(
                            kind: st.kind,
                            range: NSRange(location: st.range.location + interpStart, length: st.range.length),
                            text: st.text
                        ))
                    }
                }

                // Closing }
                if pos < chars.count && chars[pos] == "}" {
                    tokens.append(token(.stringInterp, start: pos, end: pos + 1))
                    pos += 1
                }
                segStart = pos
                continue
            }

            // Escape sequences
            if ch == "\\" && !isTriple {
                if pos > segStart {
                    tokens.append(token(.string, start: segStart, end: pos))
                }
                let escStart = pos
                pos += 1
                if pos < chars.count { pos += 1 }
                tokens.append(token(.stringEscape, start: escStart, end: pos))
                segStart = pos
                continue
            }

            pos += 1
        }

        // Unterminated
        if pos > segStart {
            tokens.append(token(.string, start: segStart, end: pos))
        }
        return tokens
    }

    private func classifyWord(_ word: String) -> TTTokenKind {
        if Self.stepChains.contains(word) { return .stepChain }
        if Self.constants.contains(word) { return .constant }
        if Self.keywords.contains(word) { return .keyword }
        if Self.classicKeywords.contains(word) { return .keywordClassic }
        if Self.operatorKeywords.contains(word) { return .operatorKw }
        if Self.typeKeywords.contains(word) { return .typeKw }
        if Self.builtins.contains(word) { return .builtin }
        return .identifier
    }

    private func token(_ kind: TTTokenKind, start: Int, end: Int) -> TTToken {
        let text = String(chars[start..<Swift.min(end, chars.count)])
        return TTToken(kind: kind, range: NSRange(location: start, length: end - start), text: text)
    }
}
