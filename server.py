"""
TinyTalk API Server + TX Blueprint
Flask-based HTTP API for running TinyTalk code, plus a Monaco-based web IDE.
TX Blueprint app available at /blueprint.

Endpoints:
    GET  /                          TinyTalk Web IDE (Monaco editor)
    GET  /blueprint                 TX Blueprint app
    POST /api/run                   Execute TinyTalk code
    POST /api/run-debug             Execute with step chain debugging
    POST /api/check                 Parse-only syntax check (returns errors)
    POST /api/transpile             Transpile to Python
    POST /api/transpile-sql         Transpile to SQL
    POST /api/transpile-js          Transpile to JavaScript
    POST /api/repl                  REPL: execute a line with persistent state
    POST /api/repl/reset            REPL: reset session
    GET  /api/health                Health check
    GET  /api/examples              List example programs
"""

import os
import re
import json
import uuid
import tempfile
from flask import Flask, request, jsonify, send_from_directory

from .kernel import TinyTalkKernel
from .stdlib import _CHART_MARKER
from .lexer import Lexer
from .parser import Parser
from .transpiler import transpile, transpile_pandas
from .sql_transpiler import transpile_sql
from .js_transpiler import transpile_js
from .runtime import ExecutionBounds

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
UPLOAD_DIR = tempfile.mkdtemp(prefix="tinytalk_uploads_")

app = Flask(__name__, static_folder=STATIC_DIR)

# Bounded execution for API requests (stricter than CLI)
API_BOUNDS = ExecutionBounds(
    max_ops=500_000,
    max_iterations=50_000,
    max_recursion=500,
    timeout_seconds=10.0,
)


@app.route("/")
def ide():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/blueprint")
def blueprint():
    return send_from_directory(os.path.join(STATIC_DIR, "blueprinting"), "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "2.0.0", "language": "TinyTalk"})


# REPL session storage (in-memory, per-session)
_repl_sessions = {}


@app.route("/api/run", methods=["POST"])
def run_code():
    data = request.get_json(force=True, silent=True) or {}
    source = data.get("code", data.get("source", ""))

    if not source:
        return jsonify({"success": False, "error": "No code provided"}), 400

    kernel = TinyTalkKernel(bounds=API_BOUNDS)
    result = kernel.run(source)

    output = result.output
    charts = []
    if result.success:
        output, charts = _extract_charts(output)

    return jsonify({
        "success": result.success,
        "output": output,
        "error": result.error or None,
        "elapsed_ms": result.elapsed_ms,
        "op_count": result.op_count,
        "charts": charts,
    })


@app.route("/api/run-debug", methods=["POST"])
def run_debug():
    """Execute with step chain debugging — returns intermediate results at each step."""
    data = request.get_json(force=True, silent=True) or {}
    source = data.get("code", data.get("source", ""))

    if not source:
        return jsonify({"success": False, "error": "No code provided"}), 400

    kernel = TinyTalkKernel(bounds=API_BOUNDS, debug_chains=True)
    result = kernel.run(source)

    output = result.output
    charts = []
    if result.success:
        output, charts = _extract_charts(output)

    return jsonify({
        "success": result.success,
        "output": output,
        "error": result.error or None,
        "elapsed_ms": result.elapsed_ms,
        "op_count": result.op_count,
        "chain_traces": kernel.get_debug_traces(),
        "charts": charts,
    })


@app.route("/api/repl", methods=["POST"])
def repl_eval():
    """REPL endpoint: execute a line with persistent state across requests."""
    data = request.get_json(force=True, silent=True) or {}
    source = data.get("code", data.get("source", ""))
    session_id = data.get("session", "")

    if not session_id:
        session_id = str(uuid.uuid4())

    # Get or create kernel for this session
    if session_id not in _repl_sessions:
        _repl_sessions[session_id] = TinyTalkKernel(bounds=API_BOUNDS, repl_mode=True)

    kernel = _repl_sessions[session_id]
    result = kernel.run(source)

    output = result.output
    charts = []
    if result.success:
        output, charts = _extract_charts(output)

    return jsonify({
        "success": result.success,
        "output": output,
        "error": result.error or None,
        "elapsed_ms": result.elapsed_ms,
        "session": session_id,
        "charts": charts,
    })


@app.route("/api/repl/reset", methods=["POST"])
def repl_reset():
    """Reset a REPL session."""
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session", "")
    if session_id in _repl_sessions:
        del _repl_sessions[session_id]
    return jsonify({"success": True, "message": "Session reset"})


@app.route("/api/check", methods=["POST"])
def check_code():
    """Parse-only syntax check with error recovery — returns multiple errors."""
    data = request.get_json(force=True, silent=True) or {}
    source = data.get("code", data.get("source", ""))

    if not source:
        return jsonify({"errors": []})

    try:
        tokens = Lexer(source).tokenize()
        # Use error-recovery mode to collect multiple errors
        parser = Parser(tokens, recover=True)
        parser.parse()
        errors = []
        for err in parser.errors:
            errors.append({
                "line": err.line, "column": err.column, "message": err.message,
            })
        return jsonify({"errors": errors})
    except SyntaxError as e:
        line, col, msg = _parse_error_location(str(e))
        return jsonify({"errors": [{"line": line, "column": col, "message": msg}]})
    except Exception as e:
        line, col, msg = _parse_error_location(str(e))
        return jsonify({"errors": [{"line": line, "column": col, "message": msg}]})


@app.route("/api/transpile", methods=["POST"])
def transpile_code():
    """Transpile TinyTalk to Python."""
    data = request.get_json(force=True, silent=True) or {}
    source = data.get("code", data.get("source", ""))
    mode = data.get("mode", "plain")  # "plain" or "pandas"

    if not source:
        return jsonify({"success": False, "error": "No code provided"}), 400

    try:
        if mode == "pandas":
            output = transpile_pandas(source)
        else:
            output = transpile(source)
        return jsonify({"success": True, "output": output})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/transpile-sql", methods=["POST"])
def transpile_sql_code():
    """Transpile TinyTalk to SQL."""
    data = request.get_json(force=True, silent=True) or {}
    source = data.get("code", data.get("source", ""))

    if not source:
        return jsonify({"success": False, "error": "No code provided"}), 400

    try:
        output = transpile_sql(source)
        return jsonify({"success": True, "output": output})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/transpile-js", methods=["POST"])
def transpile_js_code():
    """Transpile TinyTalk to JavaScript."""
    data = request.get_json(force=True, silent=True) or {}
    source = data.get("code", data.get("source", ""))

    if not source:
        return jsonify({"success": False, "error": "No code provided"}), 400

    try:
        output = transpile_js(source)
        return jsonify({"success": True, "output": output})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/examples", methods=["GET"])
def examples():
    examples_dir = os.path.join(os.path.dirname(__file__), "examples")
    result = []
    if os.path.isdir(examples_dir):
        for fname in sorted(os.listdir(examples_dir)):
            if fname.endswith(".tt"):
                with open(os.path.join(examples_dir, fname)) as f:
                    result.append({
                        "name": fname.replace(".tt", ""),
                        "filename": fname,
                        "code": f.read(),
                    })
    return jsonify(result)


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Upload a CSV or JSON file so it can be used with read_csv / read_json."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"success": False, "error": "No file selected"}), 400

    filename = os.path.basename(f.filename)
    if not filename.lower().endswith((".csv", ".json")):
        return jsonify({"success": False, "error": "Only .csv and .json files are supported"}), 400

    filepath = os.path.join(UPLOAD_DIR, filename)
    f.save(filepath)

    # Register with stdlib so read_csv/read_json can find it by name
    from .stdlib import register_uploaded_file
    register_uploaded_file(filename, filepath)

    return jsonify({"success": True, "filename": filename})


def _extract_charts(output: str):
    """Extract chart directives from program output, returning clean output and chart list."""
    charts = []
    clean_lines = []
    for line in output.split("\n"):
        if line.startswith(_CHART_MARKER):
            try:
                chart_json = line[len(_CHART_MARKER):]
                charts.append(json.loads(chart_json))
            except (json.JSONDecodeError, ValueError):
                clean_lines.append(line)
        else:
            clean_lines.append(line)
    return "\n".join(clean_lines), charts


def _parse_error_location(error_msg: str) -> tuple:
    """Extract line/column from error messages like 'Line 3: ...' or 'line 3 column 5'."""
    line, col = 1, 1
    msg = error_msg

    m = re.search(r'[Ll]ine\s+(\d+)', error_msg)
    if m:
        line = int(m.group(1))

    m2 = re.search(r'[Cc]ol(?:umn)?\s+(\d+)', error_msg)
    if m2:
        col = int(m2.group(1))

    return line, col, msg


def create_app():
    """Factory function for WSGI servers."""
    return app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, debug=True)
