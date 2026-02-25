"""
TinyTalk API Server + IDE
Flask-based HTTP API for running TinyTalk code, plus a Monaco-based web IDE.

Endpoints:
    GET  /                   Web IDE (Monaco editor)
    POST /api/run            Execute TinyTalk code
    POST /api/check          Parse-only syntax check (returns errors)
    POST /api/transpile      Transpile to Python
    POST /api/transpile-sql  Transpile to SQL
    POST /api/transpile-js   Transpile to JavaScript
    GET  /api/health         Health check
    GET  /api/examples       List example programs
"""

import os
import re
from flask import Flask, request, jsonify, send_from_directory

from .kernel import TinyTalkKernel
from .lexer import Lexer
from .parser import Parser
from .transpiler import transpile, transpile_pandas
from .sql_transpiler import transpile_sql
from .js_transpiler import transpile_js
from .runtime import ExecutionBounds

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

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


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "2.0.0", "language": "TinyTalk"})


@app.route("/api/run", methods=["POST"])
def run_code():
    data = request.get_json(force=True, silent=True) or {}
    source = data.get("code", data.get("source", ""))

    if not source:
        return jsonify({"success": False, "error": "No code provided"}), 400

    kernel = TinyTalkKernel(bounds=API_BOUNDS)
    result = kernel.run(source)

    return jsonify({
        "success": result.success,
        "output": result.output,
        "error": result.error or None,
        "elapsed_ms": result.elapsed_ms,
        "op_count": result.op_count,
    })


@app.route("/api/check", methods=["POST"])
def check_code():
    """Parse-only syntax check — returns errors with line/column info."""
    data = request.get_json(force=True, silent=True) or {}
    source = data.get("code", data.get("source", ""))

    if not source:
        return jsonify({"errors": []})

    try:
        tokens = Lexer(source).tokenize()
        Parser(tokens).parse()
        return jsonify({"errors": []})
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
