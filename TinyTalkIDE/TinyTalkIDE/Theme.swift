import SwiftUI
import AppKit

// MARK: - Catppuccin Mocha Theme (matching the web IDE)

enum TTTheme {
    // Background colors
    static let bgPrimary    = Color(hex: 0x1E1E2E)
    static let bgSecondary  = Color(hex: 0x181825)
    static let bgSurface    = Color(hex: 0x313244)
    static let bgHover      = Color(hex: 0x45475A)

    // Text colors
    static let textPrimary   = Color(hex: 0xCDD6F4)
    static let textSecondary = Color(hex: 0xA6ADC8)
    static let textMuted     = Color(hex: 0x6C7086)

    // Accent colors
    static let accent       = Color(hex: 0x89B4FA)
    static let accentGreen  = Color(hex: 0xA6E3A1)
    static let accentRed    = Color(hex: 0xF38BA8)
    static let accentYellow = Color(hex: 0xF9E2AF)
    static let accentTeal   = Color(hex: 0x94E2D5)
    static let accentPurple = Color(hex: 0xCBA6F7)
    static let accentPeach  = Color(hex: 0xFAB387)

    // Border
    static let border = Color(hex: 0x45475A)

    // NSColor equivalents for NSTextView
    static let nsBgPrimary    = NSColor(hex: 0x1E1E2E)
    static let nsBgSecondary  = NSColor(hex: 0x181825)
    static let nsTextPrimary  = NSColor(hex: 0xCDD6F4)
    static let nsTextMuted    = NSColor(hex: 0x6C7086)
    static let nsBorder       = NSColor(hex: 0x45475A)

    // Syntax colors (NSColor for attributed strings)
    static let syntaxKeyword      = NSColor(hex: 0xC586C0)  // purple
    static let syntaxStepChain    = NSColor(hex: 0x4EC9B0)  // teal, bold
    static let syntaxOperatorKw   = NSColor(hex: 0xC586C0)  // purple
    static let syntaxType         = NSColor(hex: 0x4EC9B0)  // teal
    static let syntaxBuiltin      = NSColor(hex: 0xDCDCAA)  // yellow
    static let syntaxConstant     = NSColor(hex: 0x569CD6)  // blue
    static let syntaxIdentifier   = NSColor(hex: 0x9CDCFE)  // light blue
    static let syntaxNumber       = NSColor(hex: 0xB5CEA8)  // green
    static let syntaxString       = NSColor(hex: 0xCE9178)  // orange
    static let syntaxStringEscape = NSColor(hex: 0xD7BA7D)  // gold
    static let syntaxComment      = NSColor(hex: 0x6A9955)  // green italic
    static let syntaxOperator     = NSColor(hex: 0xD4D4D4)
    static let syntaxPipe         = NSColor(hex: 0x4EC9B0)  // teal
    static let syntaxBracket      = NSColor(hex: 0xFFD700)  // gold
    static let syntaxDefault      = NSColor(hex: 0xCDD6F4)

    // Font
    static let editorFontName = "JetBrains Mono"
    static let fallbackFontName = "Menlo"
    static let editorFontSize: CGFloat = 14
    static let uiFontSize: CGFloat = 13

    static var editorFont: NSFont {
        NSFont(name: editorFontName, size: editorFontSize)
            ?? NSFont(name: fallbackFontName, size: editorFontSize)
            ?? NSFont.monospacedSystemFont(ofSize: editorFontSize, weight: .regular)
    }

    static var editorFontBold: NSFont {
        NSFont(name: "\(editorFontName)-Bold", size: editorFontSize)
            ?? NSFont(name: "\(fallbackFontName)-Bold", size: editorFontSize)
            ?? NSFont.monospacedSystemFont(ofSize: editorFontSize, weight: .bold)
    }

    static var uiMonoFont: Font {
        .system(size: uiFontSize, design: .monospaced)
    }
}

// MARK: - Color Extensions

extension Color {
    init(hex: UInt32, alpha: Double = 1.0) {
        let r = Double((hex >> 16) & 0xFF) / 255.0
        let g = Double((hex >> 8) & 0xFF) / 255.0
        let b = Double(hex & 0xFF) / 255.0
        self.init(.sRGB, red: r, green: g, blue: b, opacity: alpha)
    }
}

extension NSColor {
    convenience init(hex: UInt32, alpha: CGFloat = 1.0) {
        let r = CGFloat((hex >> 16) & 0xFF) / 255.0
        let g = CGFloat((hex >> 8) & 0xFF) / 255.0
        let b = CGFloat(hex & 0xFF) / 255.0
        self.init(srgbRed: r, green: g, blue: b, alpha: alpha)
    }
}
