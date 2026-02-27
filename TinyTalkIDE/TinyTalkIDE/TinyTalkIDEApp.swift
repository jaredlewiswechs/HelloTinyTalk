import SwiftUI

@main
struct TinyTalkIDEApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 800, minHeight: 500)
        }
        .windowStyle(.titleBar)
        .defaultSize(width: 1280, height: 800)
        .commands {
            // File menu
            CommandGroup(replacing: .newItem) {
                Button("New") {
                    // Post notification for new file
                    NotificationCenter.default.post(name: .newFile, object: nil)
                }
                .keyboardShortcut("n")
            }

            // Edit menu additions
            CommandMenu("Code") {
                Button("Run") {
                    NotificationCenter.default.post(name: .runCode, object: nil)
                }
                .keyboardShortcut(.return, modifiers: .command)

                Button("Debug") {
                    NotificationCenter.default.post(name: .debugCode, object: nil)
                }
                .keyboardShortcut(.return, modifiers: [.command, .shift])

                Divider()

                Button("Transpile to Python") {
                    NotificationCenter.default.post(name: .transpilePython, object: nil)
                }
                .keyboardShortcut("p", modifiers: [.command, .shift])

                Button("Transpile to SQL") {
                    NotificationCenter.default.post(name: .transpileSQL, object: nil)
                }

                Button("Transpile to JavaScript") {
                    NotificationCenter.default.post(name: .transpileJS, object: nil)
                }

                Divider()

                Button("Clear Output") {
                    NotificationCenter.default.post(name: .clearOutput, object: nil)
                }
                .keyboardShortcut("k", modifiers: .command)
            }
        }
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let newFile = Notification.Name("newFile")
    static let runCode = Notification.Name("runCode")
    static let debugCode = Notification.Name("debugCode")
    static let transpilePython = Notification.Name("transpilePython")
    static let transpileSQL = Notification.Name("transpileSQL")
    static let transpileJS = Notification.Name("transpileJS")
    static let clearOutput = Notification.Name("clearOutput")
}
