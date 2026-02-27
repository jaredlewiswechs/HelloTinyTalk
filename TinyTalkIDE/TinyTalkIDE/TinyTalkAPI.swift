import Foundation

// MARK: - TinyTalk Backend API Client

class TinyTalkAPI {

    static let shared = TinyTalkAPI()

    var baseURL: String = "http://localhost:5555"

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 15
        return URLSession(configuration: config)
    }()

    // MARK: - Response Types

    struct RunResponse: Decodable {
        let success: Bool
        let output: String?
        let error: String?
        let elapsed_ms: Double?
        let op_count: Int?
        let charts: [ChartSpec]?
    }

    struct DebugResponse: Decodable {
        let success: Bool
        let output: String?
        let error: String?
        let elapsed_ms: Double?
        let op_count: Int?
        let chain_traces: [ChainTrace]?
        let charts: [ChartSpec]?
    }

    struct TranspileResponse: Decodable {
        let success: Bool
        let output: String?
        let error: String?
    }

    struct CheckResponse: Decodable {
        let errors: [CheckError]
    }

    struct CheckError: Decodable {
        let line: Int?
        let column: Int?
        let message: String
    }

    struct ChainTrace: Decodable {
        let source: String
        let source_count: Int?
        let steps: [ChainStep]
    }

    struct ChainStep: Decodable {
        let step: String
        let args: String?
        let preview: String
        let count: Int?
    }

    struct ChartSpec: Decodable {
        let type: String
        let title: String?
        let labels: [String]?
        let values: [Double]?
        let x: [Double]?
        let y: [Double]?
        let series: [String: [Double]]?
    }

    struct ReplResponse: Decodable {
        let success: Bool
        let output: String?
        let error: String?
        let elapsed_ms: Double?
        let session: String?
        let charts: [ChartSpec]?
    }

    struct ExampleEntry: Decodable {
        let name: String
        let filename: String
        let code: String
    }

    // MARK: - API Methods

    func run(code: String) async throws -> RunResponse {
        return try await post(path: "/api/run", body: ["code": code])
    }

    func runDebug(code: String) async throws -> DebugResponse {
        return try await post(path: "/api/run-debug", body: ["code": code])
    }

    func repl(code: String, session: String) async throws -> ReplResponse {
        return try await post(path: "/api/repl", body: ["code": code, "session": session])
    }

    func check(code: String) async throws -> CheckResponse {
        return try await post(path: "/api/check", body: ["code": code])
    }

    func transpile(code: String, target: String) async throws -> TranspileResponse {
        let path: String
        switch target {
        case "sql":  path = "/api/transpile-sql"
        case "js":   path = "/api/transpile-js"
        default:     path = "/api/transpile"
        }
        return try await post(path: path, body: ["code": code])
    }

    func fetchExamples() async throws -> [ExampleEntry] {
        return try await get(path: "/api/examples")
    }

    // MARK: - HTTP Helpers

    private func post<T: Decodable>(path: String, body: [String: Any]) async throws -> T {
        let url = URL(string: baseURL + path)!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await session.data(for: request)

        guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else {
            throw APIError.serverError
        }

        let decoder = JSONDecoder()
        return try decoder.decode(T.self, from: data)
    }

    private func get<T: Decodable>(path: String) async throws -> T {
        let url = URL(string: baseURL + path)!
        let (data, response) = try await session.data(for: URLRequest(url: url))

        guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else {
            throw APIError.serverError
        }

        return try JSONDecoder().decode(T.self, from: data)
    }

    enum APIError: LocalizedError {
        case serverError
        case connectionFailed

        var errorDescription: String? {
            switch self {
            case .serverError: return "Server returned an error"
            case .connectionFailed: return "Could not connect to TinyTalk server"
            }
        }
    }
}
