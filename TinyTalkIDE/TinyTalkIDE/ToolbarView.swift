import SwiftUI

// MARK: - Toolbar

struct IDEToolbarView: View {
    @ObservedObject var state: IDEState
    @State private var selectedExample: String = ""

    var body: some View {
        HStack(spacing: 8) {
            // Logo
            Text("TinyTalk")
                .font(.system(size: 15, weight: .bold, design: .monospaced))
                .foregroundColor(TTTheme.accentTeal)

            Divider().frame(height: 20)

            // Run button
            Button(action: { state.runCode() }) {
                HStack(spacing: 5) {
                    Image(systemName: "play.fill")
                        .font(.system(size: 10))
                    Text("Run")
                        .font(.system(size: 13, weight: .semibold))
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 5)
                .background(TTTheme.accentGreen)
                .foregroundColor(Color(hex: 0x1E1E2E))
                .cornerRadius(6)
            }
            .buttonStyle(.plain)
            .keyboardShortcut(.return, modifiers: .command)
            .disabled(state.isRunning)
            .help("Run (\u{2318}Enter)")

            // Debug button
            ToolbarButton(title: "Debug", action: { state.runDebug() })
                .disabled(state.isRunning)
                .help("Run with step-through chain debugger")

            Divider().frame(height: 20)

            // Mode selector
            Picker("Mode", selection: Binding(
                get: { state.mode },
                set: { state.switchMode($0) }
            )) {
                ForEach(IDEMode.allCases) { mode in
                    Text(mode.rawValue).tag(mode)
                }
            }
            .pickerStyle(.menu)
            .frame(width: 100)

            // Examples
            Picker("Examples", selection: $selectedExample) {
                Text("Examples...").tag("")
                Divider()

                // Built-in examples
                ForEach(ExamplePrograms.builtIn) { example in
                    Text(example.name).tag("builtin:\(example.name)")
                }

                if !state.examples.isEmpty {
                    Divider()
                    ForEach(state.examples, id: \.name) { example in
                        Text(example.name).tag("server:\(example.name)")
                    }
                }
            }
            .pickerStyle(.menu)
            .frame(width: 130)
            .onChange(of: selectedExample) { _, newValue in
                guard !newValue.isEmpty else { return }
                if newValue.hasPrefix("builtin:") {
                    let name = String(newValue.dropFirst(8))
                    if let example = ExamplePrograms.builtIn.first(where: { $0.name == name }) {
                        state.code = example.code
                    }
                } else if newValue.hasPrefix("server:") {
                    let name = String(newValue.dropFirst(7))
                    if let example = state.examples.first(where: { $0.name == name }) {
                        state.loadExample(example)
                    }
                }
                selectedExample = ""
            }

            Spacer()

            // Transpile buttons
            ToolbarButton(title: "Python", action: { state.transpile(target: "python") })
                .disabled(state.isRunning)
                .help("Transpile to Python")

            ToolbarButton(title: "SQL", action: { state.transpile(target: "sql") })
                .disabled(state.isRunning)
                .help("Transpile to SQL")

            ToolbarButton(title: "JS", action: { state.transpile(target: "js") })
                .disabled(state.isRunning)
                .help("Transpile to JavaScript")

            Divider().frame(height: 20)

            ToolbarButton(title: "Clear", action: { state.clearOutput() })
                .help("Clear all output")

            // Server URL
            ServerURLField(url: $state.serverURL)
        }
        .padding(.horizontal, 12)
        .frame(height: 44)
        .background(TTTheme.bgSecondary)
    }
}

// MARK: - Toolbar Button

struct ToolbarButton: View {
    let title: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 13))
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(TTTheme.bgSurface)
                .foregroundColor(TTTheme.textSecondary)
                .cornerRadius(6)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Server URL Field

struct ServerURLField: View {
    @Binding var url: String
    @State private var isEditing = false

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(TTTheme.accentGreen)
                .frame(width: 6, height: 6)

            if isEditing {
                TextField("Server URL", text: $url)
                    .textFieldStyle(.plain)
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundColor(TTTheme.textSecondary)
                    .frame(width: 160)
                    .onSubmit { isEditing = false }
            } else {
                Text(url)
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundColor(TTTheme.textMuted)
                    .lineLimit(1)
                    .onTapGesture { isEditing = true }
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(TTTheme.bgSurface)
        .cornerRadius(4)
    }
}
