import SwiftUI
import AppKit

// MARK: - Code Editor (NSTextView wrapper with syntax highlighting)

struct CodeEditorView: NSViewRepresentable {
    @Binding var text: String
    var onTextChange: (() -> Void)?
    var onRun: (() -> Void)?

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    func makeNSView(context: Context) -> NSScrollView {
        let scrollView = NSScrollView()
        scrollView.hasVerticalScroller = true
        scrollView.hasHorizontalScroller = false
        scrollView.autohidesScrollers = true
        scrollView.borderType = .noBorder
        scrollView.drawsBackground = true
        scrollView.backgroundColor = TTTheme.nsBgPrimary

        let textView = TTTextView()
        textView.isEditable = true
        textView.isSelectable = true
        textView.allowsUndo = true
        textView.isRichText = false
        textView.usesFindPanel = true
        textView.isAutomaticQuoteSubstitutionEnabled = false
        textView.isAutomaticDashSubstitutionEnabled = false
        textView.isAutomaticTextReplacementEnabled = false
        textView.isAutomaticSpellingCorrectionEnabled = false
        textView.isAutomaticTextCompletionEnabled = false
        textView.smartInsertDeleteEnabled = false
        textView.isGrammarCheckingEnabled = false

        textView.font = TTTheme.editorFont
        textView.textColor = TTTheme.syntaxDefault
        textView.backgroundColor = TTTheme.nsBgPrimary
        textView.insertionPointColor = NSColor(hex: 0xF5E0DC)
        textView.selectedTextAttributes = [
            .backgroundColor: NSColor(hex: 0x45475A),
        ]

        textView.textContainerInset = NSSize(width: 12, height: 12)
        textView.isVerticallyResizable = true
        textView.isHorizontallyResizable = false
        textView.autoresizingMask = [.width]
        textView.textContainer?.containerSize = NSSize(width: 0, height: .greatestFiniteMagnitude)
        textView.textContainer?.widthTracksTextView = true

        // Line wrapping
        textView.textContainer?.lineBreakMode = .byWordWrapping
        textView.maxSize = NSSize(width: .greatestFiniteMagnitude, height: .greatestFiniteMagnitude)

        // Tab settings
        let paragraphStyle = NSMutableParagraphStyle()
        paragraphStyle.tabStops = []
        paragraphStyle.defaultTabInterval = 28.0 // ~4 spaces
        textView.defaultParagraphStyle = paragraphStyle
        textView.typingAttributes = [
            .font: TTTheme.editorFont,
            .foregroundColor: TTTheme.syntaxDefault,
            .paragraphStyle: paragraphStyle,
        ]

        textView.delegate = context.coordinator
        textView.onRunAction = onRun

        scrollView.documentView = textView
        context.coordinator.textView = textView

        // Set initial text
        textView.string = text
        SyntaxHighlighter.highlight(textView.textStorage!)

        // Enable line numbers
        let rulerView = LineNumberRulerView(textView: textView)
        scrollView.verticalRulerView = rulerView
        scrollView.hasVerticalRuler = true
        scrollView.rulersVisible = true

        return scrollView
    }

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        guard let textView = scrollView.documentView as? NSTextView else { return }
        if textView.string != text {
            let selectedRanges = textView.selectedRanges
            textView.string = text
            SyntaxHighlighter.highlight(textView.textStorage!)
            textView.selectedRanges = selectedRanges
        }
    }

    // MARK: - Coordinator

    class Coordinator: NSObject, NSTextViewDelegate {
        var parent: CodeEditorView
        weak var textView: NSTextView?
        private var isUpdating = false

        init(_ parent: CodeEditorView) {
            self.parent = parent
        }

        func textDidChange(_ notification: Notification) {
            guard let textView = notification.object as? NSTextView else { return }
            guard !isUpdating else { return }

            isUpdating = true
            parent.text = textView.string

            // Re-highlight
            SyntaxHighlighter.highlight(textView.textStorage!)

            parent.onTextChange?()
            isUpdating = false
        }

        func textView(_ textView: NSTextView, shouldChangeTextIn range: NSRange, replacementString text: String?) -> Bool {
            guard let text = text else { return true }

            // Auto-close brackets
            let autoClose: [String: String] = ["{": "}", "[": "]", "(": ")", "\"": "\""]
            if let closing = autoClose[text] {
                // Don't auto-close quotes if inside a string (simple heuristic)
                if text == "\"" {
                    let before = (textView.string as NSString).substring(to: range.location)
                    let quoteCount = before.filter { $0 == "\"" }.count
                    if quoteCount % 2 == 1 { return true }
                }

                let insert = text + closing
                textView.insertText(insert, replacementRange: range)
                // Move cursor between the pair
                let cursorPos = range.location + text.count
                textView.setSelectedRange(NSRange(location: cursorPos, length: 0))
                return false
            }

            // Auto-indent on Enter
            if text == "\n" {
                let nsString = textView.string as NSString
                let lineRange = nsString.lineRange(for: NSRange(location: range.location, length: 0))
                let currentLine = nsString.substring(with: lineRange)

                // Count leading whitespace
                var indent = ""
                for char in currentLine {
                    if char == " " || char == "\t" {
                        indent.append(char)
                    } else {
                        break
                    }
                }

                // Increase indent after {
                let trimmed = currentLine.trimmingCharacters(in: .whitespacesAndNewlines)
                if trimmed.hasSuffix("{") {
                    indent += "    "
                }

                textView.insertText("\n" + indent, replacementRange: range)
                return false
            }

            return true
        }
    }
}

// MARK: - Custom NSTextView with keyboard shortcuts

class TTTextView: NSTextView {
    var onRunAction: (() -> Void)?

    override func keyDown(with event: NSEvent) {
        // Cmd+Enter to run
        if event.modifierFlags.contains(.command) && event.keyCode == 36 {
            onRunAction?()
            return
        }
        super.keyDown(with: event)
    }
}

// MARK: - Line Number Ruler View

class LineNumberRulerView: NSRulerView {
    private weak var textView: NSTextView?

    init(textView: NSTextView) {
        self.textView = textView
        super.init(scrollView: textView.enclosingScrollView!, orientation: .verticalRuler)
        self.clientView = textView
        self.ruleThickness = 44

        NotificationCenter.default.addObserver(
            self, selector: #selector(textDidChange),
            name: NSText.didChangeNotification, object: textView
        )
        NotificationCenter.default.addObserver(
            self, selector: #selector(boundsDidChange),
            name: NSView.boundsDidChangeNotification,
            object: textView.enclosingScrollView?.contentView
        )
    }

    required init(coder: NSCoder) { fatalError("init(coder:) not supported") }

    @objc private func textDidChange(_ notification: Notification) {
        needsDisplay = true
    }

    @objc private func boundsDidChange(_ notification: Notification) {
        needsDisplay = true
    }

    override func drawHashMarksAndLabels(in rect: NSRect) {
        guard let textView = textView,
              let layoutManager = textView.layoutManager,
              let textContainer = textView.textContainer else { return }

        TTTheme.nsBgSecondary.setFill()
        rect.fill()

        // Draw separator line
        TTTheme.nsBorder.setStroke()
        let path = NSBezierPath()
        path.move(to: NSPoint(x: rect.maxX - 0.5, y: rect.minY))
        path.line(to: NSPoint(x: rect.maxX - 0.5, y: rect.maxY))
        path.lineWidth = 1
        path.stroke()

        let nsString = textView.string as NSString
        let visibleRect = textView.visibleRect
        let glyphRange = layoutManager.glyphRange(forBoundingRect: visibleRect, in: textContainer)
        let charRange = layoutManager.characterRange(forGlyphRange: glyphRange, actualGlyphRange: nil)

        let attrs: [NSAttributedString.Key: Any] = [
            .font: NSFont.monospacedSystemFont(ofSize: 11, weight: .regular),
            .foregroundColor: TTTheme.nsTextMuted,
        ]

        let activeAttrs: [NSAttributedString.Key: Any] = [
            .font: NSFont.monospacedSystemFont(ofSize: 11, weight: .regular),
            .foregroundColor: NSColor(hex: 0xCDD6F4),
        ]

        // Current line for highlighting
        let selectedRange = textView.selectedRange()
        let currentLine = nsString.lineRange(for: NSRange(location: selectedRange.location, length: 0))

        var lineNumber = 1
        // Count lines before visible range
        var idx = 0
        while idx < charRange.location && idx < nsString.length {
            if nsString.character(at: idx) == 0x0A { // \n
                lineNumber += 1
            }
            idx += 1
        }

        // Draw visible line numbers
        var charIndex = charRange.location
        while charIndex < NSMaxRange(charRange) {
            let lineRange = nsString.lineRange(for: NSRange(location: charIndex, length: 0))
            let glyphRange = layoutManager.glyphRange(forCharacterRange: lineRange, actualCharacterRange: nil)
            var lineRect = layoutManager.boundingRect(forGlyphRange: glyphRange, in: textContainer)
            lineRect.origin.y += textView.textContainerInset.height

            let isCurrentLine = NSIntersectionRange(lineRange, currentLine).length > 0
            let lineStr = "\(lineNumber)" as NSString
            let strSize = lineStr.size(withAttributes: attrs)
            let yPos = lineRect.origin.y + (lineRect.height - strSize.height) / 2 - visibleRect.origin.y + convert(NSPoint.zero, from: textView).y
            let xPos = ruleThickness - strSize.width - 8

            lineStr.draw(at: NSPoint(x: xPos, y: yPos),
                         withAttributes: isCurrentLine ? activeAttrs : attrs)

            lineNumber += 1
            charIndex = NSMaxRange(lineRange)
        }
    }
}
