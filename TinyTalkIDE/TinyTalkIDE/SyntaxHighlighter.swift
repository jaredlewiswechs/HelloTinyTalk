import AppKit

// MARK: - Syntax Highlighter

class SyntaxHighlighter {

    static func highlight(_ textStorage: NSTextStorage) {
        let source = textStorage.string
        let fullRange = NSRange(location: 0, length: (source as NSString).length)

        // Reset to default style
        textStorage.beginEditing()

        let defaultAttrs: [NSAttributedString.Key: Any] = [
            .foregroundColor: TTTheme.syntaxDefault,
            .font: TTTheme.editorFont,
        ]
        textStorage.setAttributes(defaultAttrs, range: fullRange)

        // Tokenize
        let lexer = TinyTalkLexer(source: source)
        let tokens = lexer.tokenize()

        for token in tokens {
            guard token.range.location + token.range.length <= fullRange.length else { continue }

            var attrs: [NSAttributedString.Key: Any] = [:]

            switch token.kind {
            case .keyword:
                attrs[.foregroundColor] = TTTheme.syntaxKeyword
                attrs[.font] = TTTheme.editorFont

            case .keywordClassic:
                attrs[.foregroundColor] = TTTheme.syntaxKeyword
                attrs[.font] = TTTheme.editorFont

            case .stepChain:
                attrs[.foregroundColor] = TTTheme.syntaxStepChain
                attrs[.font] = TTTheme.editorFontBold

            case .operatorKw:
                attrs[.foregroundColor] = TTTheme.syntaxOperatorKw
                attrs[.font] = TTTheme.editorFont

            case .typeKw:
                attrs[.foregroundColor] = TTTheme.syntaxType
                attrs[.font] = TTTheme.editorFont

            case .builtin:
                attrs[.foregroundColor] = TTTheme.syntaxBuiltin
                attrs[.font] = TTTheme.editorFont

            case .constant:
                attrs[.foregroundColor] = TTTheme.syntaxConstant
                attrs[.font] = TTTheme.editorFont

            case .number:
                attrs[.foregroundColor] = TTTheme.syntaxNumber
                attrs[.font] = TTTheme.editorFont

            case .string:
                attrs[.foregroundColor] = TTTheme.syntaxString
                attrs[.font] = TTTheme.editorFont

            case .stringEscape:
                attrs[.foregroundColor] = TTTheme.syntaxStringEscape
                attrs[.font] = TTTheme.editorFont

            case .stringInterp:
                attrs[.foregroundColor] = TTTheme.syntaxKeyword
                attrs[.font] = TTTheme.editorFont

            case .comment:
                attrs[.foregroundColor] = TTTheme.syntaxComment
                attrs[.font] = TTTheme.editorFont

            case .operatorSym:
                attrs[.foregroundColor] = TTTheme.syntaxOperator
                attrs[.font] = TTTheme.editorFont

            case .pipe:
                attrs[.foregroundColor] = TTTheme.syntaxPipe
                attrs[.font] = TTTheme.editorFontBold

            case .bracket:
                attrs[.foregroundColor] = TTTheme.syntaxBracket
                attrs[.font] = TTTheme.editorFont

            case .identifier:
                attrs[.foregroundColor] = TTTheme.syntaxIdentifier
                attrs[.font] = TTTheme.editorFont

            case .delimiter, .whitespace, .newline, .unknown:
                continue
            }

            textStorage.addAttributes(attrs, range: token.range)
        }

        textStorage.endEditing()
    }
}
