import SwiftUI

// MARK: - Main IDE Layout

struct ContentView: View {
    @StateObject private var state = IDEState()
    @State private var editorWidth: CGFloat = 0.55

    var body: some View {
        VStack(spacing: 0) {
            // Toolbar
            IDEToolbarView(state: state)

            Divider().background(TTTheme.border)

            // Main split: Editor | Output
            GeometryReader { geometry in
                HStack(spacing: 0) {
                    // Editor pane
                    CodeEditorView(
                        text: $state.code,
                        onTextChange: { state.scheduleCheck() },
                        onRun: { state.runCode() }
                    )
                    .frame(width: geometry.size.width * editorWidth)

                    // Resize handle
                    Rectangle()
                        .fill(TTTheme.border)
                        .frame(width: 4)
                        .contentShape(Rectangle())
                        .onHover { hovering in
                            if hovering {
                                NSCursor.resizeLeftRight.push()
                            } else {
                                NSCursor.pop()
                            }
                        }
                        .gesture(
                            DragGesture()
                                .onChanged { value in
                                    let newWidth = (value.location.x) / geometry.size.width
                                    editorWidth = min(0.8, max(0.2, newWidth))
                                }
                        )

                    // Output pane
                    OutputPanelView(state: state)
                        .frame(maxWidth: .infinity)
                }
            }

            Divider().background(TTTheme.border)

            // Status bar
            StatusBarView(state: state)
        }
        .background(TTTheme.bgSecondary)
        .preferredColorScheme(.dark)
    }
}

#Preview {
    ContentView()
        .frame(width: 1200, height: 800)
}
