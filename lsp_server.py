"""
TinyTalk LSP Server
Language Server Protocol implementation for IDE integration.

Provides:
    - Autocomplete (textDocument/completion)
    - Go-to-definition (textDocument/definition)
    - Inline errors (textDocument/publishDiagnostics)
    - Hover info (textDocument/hover)
    - Document symbols (textDocument/documentSymbol)

The AST is already there — the LSP is a wrapper around the same
parse tree the interpreter builds.

Usage:
    tinytalk lsp            Start the LSP server (stdio)
    tinytalk lsp --port N   Start on TCP port N
"""

from __future__ import annotations
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .lexer import Lexer, Token, TokenType
from .parser import Parser
from .ast_nodes import (
    ASTNode, Program, FnDecl, LetStmt, ConstStmt, StructDecl, EnumDecl,
    ImportStmt, Identifier, StepChain, Call, ForStmt,
)
from .errors import ALL_STEP_NAMES


# ---------------------------------------------------------------------------
# Document analysis
# ---------------------------------------------------------------------------

@dataclass
class Symbol:
    """A named symbol in a TinyTalk document."""
    name: str
    kind: str  # "function", "variable", "constant", "struct", "enum"
    line: int
    column: int
    end_line: int = 0
    end_column: int = 0
    detail: str = ""
    children: List["Symbol"] = field(default_factory=list)


@dataclass
class Diagnostic:
    """An error or warning in a TinyTalk document."""
    line: int
    column: int
    end_line: int
    end_column: int
    message: str
    severity: int = 1  # 1=Error, 2=Warning, 3=Info, 4=Hint


@dataclass
class Location:
    """A location in a source file."""
    line: int
    column: int


@dataclass
class CompletionItem:
    """An autocomplete suggestion."""
    label: str
    kind: str  # "function", "variable", "keyword", "step", "property"
    detail: str = ""
    insert_text: str = ""
    documentation: str = ""


class DocumentAnalyzer:
    """Analyzes a TinyTalk document for IDE features.

    This is the core of the LSP — it takes source code and produces
    symbols, diagnostics, completions, and definitions.
    """

    def __init__(self, source: str, uri: str = ""):
        self.source = source
        self.uri = uri
        self.tokens: List[Token] = []
        self.ast: Optional[Program] = None
        self.symbols: List[Symbol] = []
        self.diagnostics: List[Diagnostic] = []
        self._analyze()

    def _analyze(self):
        """Parse the document and extract all information."""
        # Tokenize (always succeeds — errors become ERROR tokens)
        try:
            self.tokens = Lexer(self.source).tokenize()
        except Exception as e:
            self.diagnostics.append(Diagnostic(
                line=1, column=1, end_line=1, end_column=1,
                message=f"Lexer error: {e}",
            ))
            return

        # Parse with error recovery
        try:
            self.ast = Parser(self.tokens).parse()
        except SyntaxError as e:
            diag = self._error_to_diagnostic(str(e))
            self.diagnostics.append(diag)
            return
        except Exception as e:
            diag = self._error_to_diagnostic(str(e))
            self.diagnostics.append(diag)
            return

        # Extract symbols from AST
        self._extract_symbols(self.ast)

    def _error_to_diagnostic(self, msg: str) -> Diagnostic:
        import re
        line, col = 1, 1
        m = re.search(r'[Ll]ine\s+(\d+)', msg)
        if m:
            line = int(m.group(1))
        m2 = re.search(r'[Cc]ol(?:umn)?\s+(\d+)', msg)
        if m2:
            col = int(m2.group(1))
        return Diagnostic(
            line=line, column=col,
            end_line=line, end_column=col + 10,
            message=msg,
        )

    def _extract_symbols(self, node: ASTNode, parent: Optional[Symbol] = None):
        """Walk the AST and extract named symbols."""
        if isinstance(node, Program):
            for stmt in node.statements:
                self._extract_symbols(stmt)

        elif isinstance(node, FnDecl):
            params = ", ".join(p[0] for p in node.params)
            sym = Symbol(
                name=node.name, kind="function",
                line=node.line, column=node.column,
                detail=f"fn {node.name}({params})",
            )
            self.symbols.append(sym)

        elif isinstance(node, LetStmt):
            detail = f"let {node.name}"
            if node.type_hint:
                detail += f": {node.type_hint}"
            sym = Symbol(
                name=node.name, kind="variable",
                line=node.line, column=node.column,
                detail=detail,
            )
            self.symbols.append(sym)

        elif isinstance(node, ConstStmt):
            sym = Symbol(
                name=node.name, kind="constant",
                line=node.line, column=node.column,
                detail=f"const {node.name}",
            )
            self.symbols.append(sym)

        elif isinstance(node, StructDecl):
            fields = ", ".join(f[0] for f in node.fields)
            sym = Symbol(
                name=node.name, kind="struct",
                line=node.line, column=node.column,
                detail=f"struct {node.name} {{{fields}}}",
            )
            self.symbols.append(sym)

        elif isinstance(node, EnumDecl):
            variants = ", ".join(v[0] for v in node.variants)
            sym = Symbol(
                name=node.name, kind="enum",
                line=node.line, column=node.column,
                detail=f"enum {node.name} {{{variants}}}",
            )
            self.symbols.append(sym)

    def get_diagnostics(self) -> List[dict]:
        """Return diagnostics as LSP-compatible dicts."""
        return [{
            "range": {
                "start": {"line": d.line - 1, "character": d.column - 1},
                "end": {"line": d.end_line - 1, "character": d.end_column - 1},
            },
            "severity": d.severity,
            "message": d.message,
            "source": "tinytalk",
        } for d in self.diagnostics]

    def get_symbols(self) -> List[dict]:
        """Return document symbols as LSP-compatible dicts."""
        kind_map = {
            "function": 12, "variable": 13, "constant": 14,
            "struct": 23, "enum": 10,
        }
        return [{
            "name": s.name,
            "kind": kind_map.get(s.kind, 13),
            "range": {
                "start": {"line": s.line - 1, "character": s.column - 1},
                "end": {"line": s.line - 1, "character": s.column + len(s.name) - 1},
            },
            "selectionRange": {
                "start": {"line": s.line - 1, "character": s.column - 1},
                "end": {"line": s.line - 1, "character": s.column + len(s.name) - 1},
            },
            "detail": s.detail,
        } for s in self.symbols]

    def get_completions(self, line: int, column: int) -> List[dict]:
        """Return completion items for the given position."""
        # Determine context from surrounding text
        lines = self.source.splitlines()
        if line < 1 or line > len(lines):
            return []
        text_before = lines[line - 1][:column - 1] if column > 0 else ""

        items = []

        # After underscore: step chain completions
        if text_before.rstrip().endswith("_") or "_" in text_before.split()[-1:]:
            for step in ALL_STEP_NAMES:
                items.append({
                    "label": step,
                    "kind": 2,  # Method
                    "detail": f"Step chain: {step}",
                    "insertText": step,
                })
            return items

        # After dot: property completions
        if text_before.rstrip().endswith("."):
            for prop, desc in [
                ("str", "Convert to string"), ("int", "Convert to integer"),
                ("float", "Convert to float"), ("bool", "Convert to boolean"),
                ("type", "Get type name"), ("len", "Get length"),
                ("upcase", "Uppercase"), ("downcase", "Lowercase"),
                ("trim", "Strip whitespace"), ("chars", "Split to chars"),
                ("words", "Split to words"), ("reversed", "Reverse"),
            ]:
                items.append({
                    "label": prop, "kind": 10, "detail": desc,
                    "insertText": prop,
                })
            return items

        # Default: keywords + user symbols
        for kw in ["let", "const", "fn", "return", "if", "else", "elif",
                    "for", "while", "match", "struct", "try", "catch",
                    "from", "import", "show", "print"]:
            items.append({"label": kw, "kind": 14, "insertText": kw})

        for sym in self.symbols:
            items.append({
                "label": sym.name,
                "kind": 3 if sym.kind == "function" else 6,
                "detail": sym.detail,
                "insertText": sym.name,
            })

        return items

    def get_definition(self, line: int, column: int) -> Optional[dict]:
        """Find the definition location of the symbol at the given position."""
        # Find the token at the given position
        target_name = self._get_word_at(line, column)
        if not target_name:
            return None

        # Search symbols for definition
        for sym in self.symbols:
            if sym.name == target_name:
                return {
                    "uri": self.uri,
                    "range": {
                        "start": {"line": sym.line - 1, "character": sym.column - 1},
                        "end": {"line": sym.line - 1, "character": sym.column + len(sym.name) - 1},
                    },
                }
        return None

    def get_hover(self, line: int, column: int) -> Optional[dict]:
        """Get hover information for the symbol at the given position."""
        target_name = self._get_word_at(line, column)
        if not target_name:
            return None

        # Check user-defined symbols
        for sym in self.symbols:
            if sym.name == target_name:
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": f"```tinytalk\n{sym.detail}\n```",
                    }
                }

        # Check step chains
        if target_name.startswith("_") and target_name in ALL_STEP_NAMES:
            from .errors import step_args_hint
            hint = step_args_hint(target_name)
            return {
                "contents": {
                    "kind": "markdown",
                    "value": f"**Step Chain**: `{target_name}`\n\n{hint}",
                }
            }

        return None

    def _get_word_at(self, line: int, column: int) -> Optional[str]:
        """Extract the word at the given line/column position."""
        lines = self.source.splitlines()
        if line < 1 or line > len(lines):
            return None
        text = lines[line - 1]
        if column < 1 or column > len(text):
            return None
        # Find word boundaries
        start = column - 1
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "_"):
            start -= 1
        end = column - 1
        while end < len(text) and (text[end].isalnum() or text[end] == "_"):
            end += 1
        word = text[start:end]
        return word if word else None


# ---------------------------------------------------------------------------
# LSP JSON-RPC server
# ---------------------------------------------------------------------------

class TinyTalkLSP:
    """Minimal LSP server for TinyTalk.

    Communicates via JSON-RPC over stdio (standard LSP transport).
    """

    def __init__(self):
        self.documents: Dict[str, str] = {}
        self.analyzers: Dict[str, DocumentAnalyzer] = {}
        self.running = False

    def start(self):
        """Start the LSP server on stdio."""
        self.running = True
        while self.running:
            try:
                msg = self._read_message()
                if msg is None:
                    break
                response = self._handle_message(msg)
                if response:
                    self._write_message(response)
            except Exception:
                break

    def _read_message(self) -> Optional[dict]:
        """Read a JSON-RPC message from stdin."""
        headers = {}
        while True:
            line = sys.stdin.buffer.readline().decode("utf-8")
            if not line or line == "\r\n":
                break
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip()] = val.strip()
        content_length = int(headers.get("Content-Length", 0))
        if content_length == 0:
            return None
        body = sys.stdin.buffer.read(content_length).decode("utf-8")
        return json.loads(body)

    def _write_message(self, msg: dict):
        """Write a JSON-RPC message to stdout."""
        body = json.dumps(msg)
        header = f"Content-Length: {len(body)}\r\n\r\n"
        sys.stdout.buffer.write(header.encode("utf-8"))
        sys.stdout.buffer.write(body.encode("utf-8"))
        sys.stdout.buffer.flush()

    def _handle_message(self, msg: dict) -> Optional[dict]:
        """Route a JSON-RPC message to the appropriate handler."""
        method = msg.get("method", "")
        params = msg.get("params", {})
        msg_id = msg.get("id")

        if method == "initialize":
            return self._respond(msg_id, {
                "capabilities": {
                    "textDocumentSync": 1,  # Full sync
                    "completionProvider": {"triggerCharacters": ["_", ".", " "]},
                    "hoverProvider": True,
                    "definitionProvider": True,
                    "documentSymbolProvider": True,
                },
                "serverInfo": {"name": "tinytalk-lsp", "version": "1.0.0"},
            })

        if method == "initialized":
            return None

        if method == "shutdown":
            self.running = False
            return self._respond(msg_id, None)

        if method == "textDocument/didOpen":
            doc = params.get("textDocument", {})
            uri = doc.get("uri", "")
            text = doc.get("text", "")
            self.documents[uri] = text
            self._analyze_document(uri)
            return None

        if method == "textDocument/didChange":
            doc = params.get("textDocument", {})
            uri = doc.get("uri", "")
            changes = params.get("contentChanges", [])
            if changes:
                self.documents[uri] = changes[-1].get("text", "")
                self._analyze_document(uri)
            return None

        if method == "textDocument/completion":
            uri = params.get("textDocument", {}).get("uri", "")
            pos = params.get("position", {})
            analyzer = self.analyzers.get(uri)
            if analyzer:
                items = analyzer.get_completions(pos.get("line", 0) + 1, pos.get("character", 0) + 1)
                return self._respond(msg_id, {"isIncomplete": False, "items": items})
            return self._respond(msg_id, {"isIncomplete": False, "items": []})

        if method == "textDocument/hover":
            uri = params.get("textDocument", {}).get("uri", "")
            pos = params.get("position", {})
            analyzer = self.analyzers.get(uri)
            if analyzer:
                hover = analyzer.get_hover(pos.get("line", 0) + 1, pos.get("character", 0) + 1)
                return self._respond(msg_id, hover)
            return self._respond(msg_id, None)

        if method == "textDocument/definition":
            uri = params.get("textDocument", {}).get("uri", "")
            pos = params.get("position", {})
            analyzer = self.analyzers.get(uri)
            if analyzer:
                defn = analyzer.get_definition(pos.get("line", 0) + 1, pos.get("character", 0) + 1)
                return self._respond(msg_id, defn)
            return self._respond(msg_id, None)

        if method == "textDocument/documentSymbol":
            uri = params.get("textDocument", {}).get("uri", "")
            analyzer = self.analyzers.get(uri)
            if analyzer:
                return self._respond(msg_id, analyzer.get_symbols())
            return self._respond(msg_id, [])

        if msg_id is not None:
            return self._respond(msg_id, None)
        return None

    def _analyze_document(self, uri: str):
        """Re-analyze a document and publish diagnostics."""
        source = self.documents.get(uri, "")
        analyzer = DocumentAnalyzer(source, uri)
        self.analyzers[uri] = analyzer

        # Publish diagnostics
        self._write_message({
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {
                "uri": uri,
                "diagnostics": analyzer.get_diagnostics(),
            },
        })

    def _respond(self, msg_id, result) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
