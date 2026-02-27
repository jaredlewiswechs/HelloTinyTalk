import SwiftUI

// MARK: - IDE State (Observable)

enum OutputTab: String, CaseIterable, Identifiable {
    case output = "Output"
    case debug  = "Debug"
    case python = "Python"
    case sql    = "SQL"
    case js     = "JS"

    var id: String { rawValue }
}

enum IDEMode: String, CaseIterable, Identifiable {
    case program = "Program"
    case repl    = "REPL"

    var id: String { rawValue }
}

@MainActor
class IDEState: ObservableObject {
    @Published var code: String = ExamplePrograms.defaultCode
    @Published var output: String = ""
    @Published var debugOutput: String = ""
    @Published var pythonOutput: String = ""
    @Published var sqlOutput: String = ""
    @Published var jsOutput: String = ""
    @Published var statusMessage: String = "Ready"
    @Published var statusStats: String = ""
    @Published var activeTab: OutputTab = .output
    @Published var isRunning: Bool = false
    @Published var isError: Bool = false
    @Published var mode: IDEMode = .program
    @Published var serverURL: String = "http://localhost:5555"
    @Published var examples: [TinyTalkAPI.ExampleEntry] = []
    @Published var checkErrors: [TinyTalkAPI.CheckError] = []

    private var replSession: String = ""
    private var replHistory: [String] = []
    private var checkTask: Task<Void, Never>?

    private let api = TinyTalkAPI.shared

    init() {
        loadExamples()
    }

    // MARK: - Run Code

    func runCode() {
        guard !code.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        if mode == .repl {
            replEval()
            return
        }

        isRunning = true
        isError = false
        statusMessage = "Running..."
        statusStats = ""
        output = ""
        activeTab = .output

        Task {
            do {
                api.baseURL = serverURL
                let result = try await api.run(code: code)
                if result.success {
                    output = result.output ?? "(no output)"
                    isError = false
                    let ms = result.elapsed_ms.map { String(format: "%.0fms", $0) } ?? ""
                    let ops = result.op_count.map { "\($0) ops" } ?? ""
                    statusMessage = "Done"
                    statusStats = [ms, ops].filter { !$0.isEmpty }.joined(separator: " | ")
                } else {
                    output = "Error: \(result.error ?? "Unknown error")"
                    isError = true
                    statusMessage = "Error"
                    statusStats = result.elapsed_ms.map { String(format: "%.0fms", $0) } ?? ""
                }
            } catch {
                output = "Connection error: \(error.localizedDescription)\n\nMake sure the TinyTalk server is running:\n  python -m HelloTinyTalk.server"
                isError = true
                statusMessage = "Error"
                statusStats = ""
            }
            isRunning = false
        }
    }

    // MARK: - Debug

    func runDebug() {
        guard !code.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        isRunning = true
        isError = false
        statusMessage = "Debugging..."
        statusStats = ""
        output = ""
        debugOutput = ""

        Task {
            do {
                api.baseURL = serverURL
                let result = try await api.runDebug(code: code)
                if result.success {
                    output = result.output ?? "(no output)"
                    isError = false

                    // Format debug traces
                    if let traces = result.chain_traces, !traces.isEmpty {
                        debugOutput = formatTraces(traces)
                        activeTab = .debug
                    } else {
                        debugOutput = "No step chains found in this program.\nAdd step chains like: data _filter(...) _sort _take(3)"
                        activeTab = .output
                    }

                    let ms = result.elapsed_ms.map { String(format: "%.0fms", $0) } ?? ""
                    let ops = result.op_count.map { "\($0) ops" } ?? ""
                    statusMessage = "Done (debug)"
                    statusStats = [ms, ops].filter { !$0.isEmpty }.joined(separator: " | ")
                } else {
                    output = "Error: \(result.error ?? "Unknown error")"
                    isError = true
                    statusMessage = "Error"
                    statusStats = result.elapsed_ms.map { String(format: "%.0fms", $0) } ?? ""
                    activeTab = .output
                }
            } catch {
                output = "Connection error: \(error.localizedDescription)"
                isError = true
                statusMessage = "Error"
                statusStats = ""
                activeTab = .output
            }
            isRunning = false
        }
    }

    // MARK: - REPL

    private func replEval() {
        isRunning = true
        isError = false
        statusMessage = "Evaluating..."

        Task {
            do {
                api.baseURL = serverURL
                let result = try await api.repl(code: code, session: replSession)
                replSession = result.session ?? replSession
                replHistory.append(code)

                let prefix = ">> \(code.components(separatedBy: "\n").first ?? "")" +
                    (code.contains("\n") ? " ..." : "")

                if result.success {
                    output += prefix + "\n" + (result.output ?? "") + "\n"
                    isError = false
                    statusMessage = "REPL"
                    statusStats = result.elapsed_ms.map { String(format: "%.0fms", $0) } ?? ""
                } else {
                    output += prefix + "\nError: \(result.error ?? "Unknown")\n"
                    statusMessage = "REPL error"
                    statusStats = result.elapsed_ms.map { String(format: "%.0fms", $0) } ?? ""
                }
            } catch {
                output += "Network error: \(error.localizedDescription)\n"
                statusMessage = "Error"
                statusStats = ""
            }
            isRunning = false
        }
    }

    // MARK: - Transpile

    func transpile(target: String) {
        guard !code.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        isRunning = true
        statusMessage = "Transpiling to \(target)..."

        Task {
            do {
                api.baseURL = serverURL
                let result = try await api.transpile(code: code, target: target)
                if result.success {
                    switch target {
                    case "sql":    sqlOutput = result.output ?? ""
                    case "js":     jsOutput = result.output ?? ""
                    default:       pythonOutput = result.output ?? ""
                    }
                    statusMessage = "Transpiled to \(target)"
                    isError = false
                } else {
                    let errMsg = "Error: \(result.error ?? "Unknown")"
                    switch target {
                    case "sql":    sqlOutput = errMsg
                    case "js":     jsOutput = errMsg
                    default:       pythonOutput = errMsg
                    }
                    statusMessage = "Transpile error"
                    isError = true
                }
                switch target {
                case "sql":    activeTab = .sql
                case "js":     activeTab = .js
                default:       activeTab = .python
                }
            } catch {
                let errMsg = "Connection error: \(error.localizedDescription)"
                switch target {
                case "sql":    sqlOutput = errMsg
                case "js":     jsOutput = errMsg
                default:       pythonOutput = errMsg
                }
                statusMessage = "Error"
                isError = true
            }
            isRunning = false
        }
    }

    // MARK: - Syntax Check

    func scheduleCheck() {
        checkTask?.cancel()
        checkTask = Task {
            try? await Task.sleep(nanoseconds: 600_000_000) // 600ms debounce
            guard !Task.isCancelled else { return }
            await performCheck()
        }
    }

    private func performCheck() async {
        let source = code
        guard !source.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            checkErrors = []
            return
        }

        do {
            api.baseURL = serverURL
            let result = try await api.check(code: source)
            if !Task.isCancelled {
                checkErrors = result.errors
            }
        } catch {
            // Silently ignore check errors
        }
    }

    // MARK: - Examples

    func loadExamples() {
        Task {
            do {
                api.baseURL = serverURL
                examples = try await api.fetchExamples()
            } catch {
                // Silently ignore — examples are optional
            }
        }
    }

    func loadExample(_ example: TinyTalkAPI.ExampleEntry) {
        code = example.code
    }

    // MARK: - Clear

    func clearOutput() {
        output = ""
        debugOutput = ""
        pythonOutput = ""
        sqlOutput = ""
        jsOutput = ""
        isError = false
        statusMessage = "Cleared"
        statusStats = ""
    }

    // MARK: - Mode switching

    func switchMode(_ newMode: IDEMode) {
        mode = newMode
        if newMode == .repl {
            replSession = ""
            replHistory = []
            output = "REPL mode active. Type code and press \u{2318}Enter.\nState persists between executions.\n\n"
            statusMessage = "REPL mode"
            statusStats = "State persists across runs"
        } else {
            statusMessage = "Program mode"
            statusStats = ""
        }
    }

    // MARK: - Helpers

    private func formatTraces(_ traces: [TinyTalkAPI.ChainTrace]) -> String {
        var result = ""
        for (i, trace) in traces.enumerated() {
            result += "Chain #\(i + 1)\n"
            result += "  source: \(trace.source)"
            if let count = trace.source_count { result += " (\(count) items)" }
            result += "\n"

            for step in trace.steps {
                result += "    \u{2193}\n"
                result += "    \(step.step)"
                if let args = step.args { result += "(\(args))" }
                result += "\n"
                result += "    \u{2192} \(step.preview)"
                if let count = step.count { result += " (\(count) items)" }
                result += "\n"
            }
            result += "\n"
        }
        return result
    }
}
