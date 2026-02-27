import SwiftUI

// MARK: - Status Bar

struct StatusBarView: View {
    @ObservedObject var state: IDEState

    var body: some View {
        HStack {
            // Status indicator
            HStack(spacing: 6) {
                if state.isRunning {
                    ProgressView()
                        .controlSize(.small)
                        .scaleEffect(0.7)
                }

                Text(state.statusMessage)
                    .font(.system(size: 12))
                    .foregroundColor(state.isError ? TTTheme.accentRed : TTTheme.textMuted)
            }

            Spacer()

            // Error count (from syntax check)
            if !state.checkErrors.isEmpty {
                HStack(spacing: 4) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 10))
                        .foregroundColor(TTTheme.accentYellow)
                    Text("\(state.checkErrors.count) issue\(state.checkErrors.count == 1 ? "" : "s")")
                        .font(.system(size: 11))
                        .foregroundColor(TTTheme.accentYellow)
                }
                .padding(.horizontal, 8)
            }

            // Stats
            if !state.statusStats.isEmpty {
                Text(state.statusStats)
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundColor(TTTheme.textMuted)
            }
        }
        .padding(.horizontal, 12)
        .frame(height: 28)
        .background(TTTheme.bgSecondary)
    }
}
