import SwiftUI

// MARK: - Output Panel with Tabs

struct OutputPanelView: View {
    @ObservedObject var state: IDEState

    var body: some View {
        VStack(spacing: 0) {
            // Tab bar
            HStack(spacing: 0) {
                ForEach(OutputTab.allCases) { tab in
                    TabButton(
                        title: tab.rawValue,
                        isActive: state.activeTab == tab
                    ) {
                        state.activeTab = tab
                    }
                }
                Spacer()
            }
            .padding(.horizontal, 8)
            .frame(height: 36)
            .background(TTTheme.bgSecondary)

            Divider().background(TTTheme.border)

            // Panel content
            ZStack {
                switch state.activeTab {
                case .output:
                    OutputTextView(
                        text: state.output,
                        isError: state.isError
                    )
                case .debug:
                    OutputTextView(
                        text: state.debugOutput.isEmpty
                            ? "No step chains found.\nAdd step chains like: data _filter(...) _sort _take(3)"
                            : state.debugOutput,
                        isError: false,
                        isMuted: state.debugOutput.isEmpty
                    )
                case .python:
                    OutputTextView(
                        text: state.pythonOutput.isEmpty ? "Click \"Python\" in the toolbar to transpile." : state.pythonOutput,
                        isError: false,
                        isMuted: state.pythonOutput.isEmpty
                    )
                case .sql:
                    OutputTextView(
                        text: state.sqlOutput.isEmpty ? "Click \"SQL\" in the toolbar to transpile." : state.sqlOutput,
                        isError: false,
                        isMuted: state.sqlOutput.isEmpty
                    )
                case .js:
                    OutputTextView(
                        text: state.jsOutput.isEmpty ? "Click \"JS\" in the toolbar to transpile." : state.jsOutput,
                        isError: false,
                        isMuted: state.jsOutput.isEmpty
                    )
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(TTTheme.bgPrimary)
        }
    }
}

// MARK: - Tab Button

struct TabButton: View {
    let title: String
    let isActive: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 0) {
                Spacer()
                Text(title.uppercased())
                    .font(.system(size: 11, weight: .medium))
                    .tracking(0.5)
                    .foregroundColor(isActive ? TTTheme.accent : TTTheme.textMuted)
                    .padding(.horizontal, 14)
                Spacer()
                Rectangle()
                    .fill(isActive ? TTTheme.accent : Color.clear)
                    .frame(height: 2)
            }
        }
        .buttonStyle(.plain)
        .contentShape(Rectangle())
    }
}

// MARK: - Output Text View

struct OutputTextView: View {
    let text: String
    var isError: Bool = false
    var isMuted: Bool = false

    var body: some View {
        ScrollView(.vertical) {
            ScrollViewReader { proxy in
                Text(text)
                    .font(.system(size: 13, design: .monospaced))
                    .foregroundColor(
                        isError ? TTTheme.accentRed :
                        isMuted ? TTTheme.textMuted :
                        TTTheme.textPrimary
                    )
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .topLeading)
                    .padding(12)
                    .id("bottom")
            }
        }
        .background(TTTheme.bgPrimary)
    }
}
