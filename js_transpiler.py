"""
TinyTalk → JavaScript Transpiler

Converts TinyTalk code to equivalent JavaScript. This is a teaching tool:
students write TinyTalk pipelines and see the JavaScript equivalent,
bridging data manipulation concepts to industry JavaScript/Node.js.

Mapping:
    let x = 10              →  let x = 10;
    const PI = 3.14         →  const PI = 3.14;
    fn add(a, b) { ... }   →  function add(a, b) { ... }
    (x) => x * 2           →  (x) => x * 2
    show(x)                 →  console.log(x)
    _filter(pred)           →  .filter(pred)
    _map(fn)                →  .map(fn)
    _sort                   →  .slice().sort(...)
    _reduce(fn, init)       →  .reduce(fn, init)
    _take(n)                →  .slice(0, n)
    _drop(n)                →  .slice(n)
    _reverse                →  .slice().reverse()
    _first                  →  [0]
    _last                   →  .at(-1)
    _unique                 →  [...new Set(...)]
    _flatten                →  .flat()
    _sum                    →  .reduce((a, b) => a + b, 0)
    _avg                    →  (arr => arr.reduce((a,b)=>a+b,0)/arr.length)
    _count                  →  .length
    _min / _max             →  Math.min(...) / Math.max(...)
    _group(fn)              →  Object.groupBy(...)
    _each(fn)               →  .forEach(fn)
    _chunk(n)               →  chunked via helper
    _join / _leftJoin       →  nested loops / flatMap

Usage:
    from newTinyTalk.js_transpiler import transpile_js

    js = transpile_js('let x = [1,2,3] _filter((n) => n > 1) _sum')
"""

from .ast_nodes import (
    ASTNode, Program, Literal, Identifier, BinaryOp, UnaryOp, Call, Index,
    Member, Array, MapLiteral, Lambda, Conditional, Range, Pipe, StepChain,
    StringInterp, LetStmt, ConstStmt, AssignStmt, Block, IfStmt, ForStmt,
    WhileStmt, ReturnStmt, BreakStmt, ContinueStmt, FnDecl, StructDecl,
    EnumDecl, MatchStmt, TryStmt, ThrowStmt,
)
from .lexer import Lexer
from .parser import Parser


# ---------------------------------------------------------------------------
# Built-in function mappings: TinyTalk name → JavaScript expression template
# ---------------------------------------------------------------------------

_BUILTIN_MAP = {
    "show": "console.log({args})",
    "println": "console.log({args})",
    "print": "process.stdout.write(String({args}))",
    "len": "{0}.length",
    "type": "typeof {0}",
    "typeof": "typeof {0}",
    "str": "String({0})",
    "int": "Math.trunc(Number({0}))",
    "float": "Number({0})",
    "bool": "Boolean({0})",
    "range": "Array.from({{length: {0}}}, (_, i) => i)",
    "append": "{0}.push({1})",
    "push": "{0}.push({1})",
    "pop": "{0}.pop()",
    "keys": "Object.keys({0})",
    "values": "Object.values({0})",
    "contains": "{0}.includes({1})",
    "reverse": "{0}.slice().reverse()",
    "sort": "{0}.slice().sort((a, b) => a - b)",
    "abs": "Math.abs({0})",
    "round": "Math.round({args})",
    "floor": "Math.floor({0})",
    "ceil": "Math.ceil({0})",
    "sqrt": "Math.sqrt({0})",
    "pow": "Math.pow({0}, {1})",
    "sin": "Math.sin({0})",
    "cos": "Math.cos({0})",
    "tan": "Math.tan({0})",
    "log": "Math.log({0})",
    "exp": "Math.exp({0})",
    "sum": "{0}.reduce((a, b) => a + b, 0)",
    "min": "Math.min({args})",
    "max": "Math.max({args})",
    "split": "{0}.split({1})",
    "join": "{0}.join({1})",
    "replace": "{0}.replace({1}, {2})",
    "trim": "{0}.trim()",
    "upcase": "{0}.toUpperCase()",
    "downcase": "{0}.toLowerCase()",
    "startswith": "{0}.startsWith({1})",
    "endswith": "{0}.endsWith({1})",
    "zip": "{0}.map((e, i) => [e, {1}[i]])",
    "enumerate": "{0}.map((v, i) => [i, v])",
    "hash": "/* hash not available in plain JS */",
    "read_csv": "/* read_csv: use a CSV library */",
    "write_csv": "/* write_csv: use a CSV library */",
    "parse_json": "JSON.parse({0})",
    "to_json": "JSON.stringify({0})",
    "read_json": "JSON.parse(require('fs').readFileSync({0}, 'utf8'))",
    "write_json": "require('fs').writeFileSync({1}, JSON.stringify({0}, null, 2))",
}

# Operator mappings: TinyTalk → JavaScript
_OP_MAP = {
    "==": "===",
    "!=": "!==",
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "/",
    "//": "Math.trunc({left} / {right})",
    "%": "%",
    "**": "**",
    "<": "<",
    ">": ">",
    "<=": "<=",
    ">=": ">=",
    "and": "&&",
    "or": "||",
    "is": "===",
    "isnt": "!==",
    "&": "&",
    "|": "|",
    "^": "^",
    "<<": "<<",
    ">>": ">>",
}


class JavaScriptTranspiler:
    """Transpiles TinyTalk AST to JavaScript code."""

    def __init__(self):
        self._indent = 0
        self._lines: list[str] = []

    def transpile(self, source: str) -> str:
        """Parse and transpile TinyTalk source to JavaScript."""
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        return self.emit(ast)

    def emit(self, node: ASTNode) -> str:
        """Emit JavaScript code from an AST."""
        self._indent = 0
        self._lines = []

        if isinstance(node, Program):
            for stmt in node.statements:
                line = self._emit_stmt(stmt)
                if line is not None:
                    self._lines.append(line)
        else:
            self._lines.append(self._emit_expr(node))

        return "\n".join(self._lines)

    # -------------------------------------------------------------------
    # Statements
    # -------------------------------------------------------------------

    def _emit_stmt(self, node: ASTNode) -> str:
        """Emit a statement, returning the line(s) as a string."""
        indent = "  " * self._indent

        if isinstance(node, LetStmt):
            if node.value is not None:
                return f"{indent}let {node.name} = {self._emit_expr(node.value)};"
            return f"{indent}let {node.name};"

        if isinstance(node, ConstStmt):
            return f"{indent}const {node.name} = {self._emit_expr(node.value)};"

        if isinstance(node, AssignStmt):
            target = self._emit_expr(node.target)
            value = self._emit_expr(node.value)
            return f"{indent}{target} {node.op} {value};"

        if isinstance(node, IfStmt):
            lines = []
            lines.append(f"{indent}if ({self._emit_expr(node.condition)}) {{")
            lines.extend(self._emit_block_body(node.then_branch))
            for cond, body in node.elif_branches:
                lines.append(f"{indent}}} else if ({self._emit_expr(cond)}) {{")
                lines.extend(self._emit_block_body(body))
            if node.else_branch:
                lines.append(f"{indent}}} else {{")
                lines.extend(self._emit_block_body(node.else_branch))
            lines.append(f"{indent}}}")
            return "\n".join(lines)

        if isinstance(node, ForStmt):
            lines = []
            lines.append(f"{indent}for (const {node.var} of {self._emit_expr(node.iterable)}) {{")
            lines.extend(self._emit_block_body(node.body))
            lines.append(f"{indent}}}")
            return "\n".join(lines)

        if isinstance(node, WhileStmt):
            lines = []
            lines.append(f"{indent}while ({self._emit_expr(node.condition)}) {{")
            lines.extend(self._emit_block_body(node.body))
            lines.append(f"{indent}}}")
            return "\n".join(lines)

        if isinstance(node, ReturnStmt):
            if node.value:
                return f"{indent}return {self._emit_expr(node.value)};"
            return f"{indent}return;"

        if isinstance(node, BreakStmt):
            return f"{indent}break;"

        if isinstance(node, ContinueStmt):
            return f"{indent}continue;"

        if isinstance(node, FnDecl):
            params = ", ".join(p[0] for p in node.params)
            lines = [f"{indent}function {node.name}({params}) {{"]
            lines.extend(self._emit_block_body(node.body))
            lines.append(f"{indent}}}")
            return "\n".join(lines)

        if isinstance(node, Block):
            stmts = []
            for s in node.statements:
                line = self._emit_stmt(s)
                if line is not None:
                    stmts.append(line)
            return "\n".join(stmts) if stmts else ""

        if isinstance(node, TryStmt):
            lines = [f"{indent}try {{"]
            lines.extend(self._emit_block_body(node.body))
            if node.catch_body:
                var = node.catch_var or "e"
                lines.append(f"{indent}}} catch ({var}) {{")
                lines.extend(self._emit_block_body(node.catch_body))
            lines.append(f"{indent}}}")
            return "\n".join(lines)

        if isinstance(node, ThrowStmt):
            return f"{indent}throw new Error({self._emit_expr(node.value)});"

        if isinstance(node, MatchStmt):
            lines = []
            val_expr = self._emit_expr(node.value)
            lines.append(f"{indent}switch ({val_expr}) {{")
            self._indent += 1
            inner_indent = "  " * self._indent
            for pattern, body in node.cases:
                lines.append(f"{inner_indent}case {self._emit_expr(pattern)}:")
                self._indent += 1
                if isinstance(body, Block):
                    for s in body.statements:
                        line = self._emit_stmt(s)
                        if line is not None:
                            lines.append(line)
                else:
                    line = self._emit_stmt(body)
                    if line is not None:
                        lines.append(line)
                lines.append(f"{'  ' * self._indent}break;")
                self._indent -= 1
            self._indent -= 1
            lines.append(f"{indent}}}")
            return "\n".join(lines)

        if isinstance(node, StructDecl):
            lines = [f"{indent}class {node.name} {{"]
            self._indent += 1
            inner = "  " * self._indent
            # Constructor with fields
            field_names = [f[0] for f in node.fields]
            params = ", ".join(field_names)
            lines.append(f"{inner}constructor({params}) {{")
            self._indent += 1
            for fname in field_names:
                lines.append(f"{'  ' * self._indent}this.{fname} = {fname};")
            self._indent -= 1
            lines.append(f"{inner}}}")
            # Methods
            for kind, method in node.methods:
                m_params = ", ".join(p[0] for p in method.params)
                lines.append(f"{inner}{method.name}({m_params}) {{")
                lines.extend(self._emit_block_body(method.body))
                lines.append(f"{inner}}}")
            self._indent -= 1
            lines.append(f"{indent}}}")
            return "\n".join(lines)

        if isinstance(node, EnumDecl):
            lines = [f"{indent}const {node.name} = Object.freeze({{"]
            self._indent += 1
            inner = "  " * self._indent
            for i, (variant_name, *_rest) in enumerate(node.variants):
                lines.append(f"{inner}{variant_name}: {i},")
            self._indent -= 1
            lines.append(f"{indent}}});")
            return "\n".join(lines)

        # Expression statement
        return f"{indent}{self._emit_expr(node)};"

    def _emit_block_body(self, node: ASTNode) -> list[str]:
        """Emit the body of a block, indented one level."""
        self._indent += 1
        if isinstance(node, Block):
            lines = []
            for s in node.statements:
                line = self._emit_stmt(s)
                if line is not None:
                    lines.append(line)
        else:
            line = self._emit_stmt(node)
            lines = [line] if line is not None else []
        self._indent -= 1
        return lines

    # -------------------------------------------------------------------
    # Expressions
    # -------------------------------------------------------------------

    def _emit_expr(self, node: ASTNode) -> str:
        if isinstance(node, Literal):
            return self._emit_literal(node)

        if isinstance(node, Identifier):
            name_map = {
                "true": "true", "false": "false", "null": "null",
                "PI": "Math.PI", "E": "Math.E", "TAU": "2 * Math.PI",
                "INF": "Infinity",
            }
            return name_map.get(node.name, node.name)

        if isinstance(node, BinaryOp):
            return self._emit_binary(node)

        if isinstance(node, UnaryOp):
            return self._emit_unary(node)

        if isinstance(node, Call):
            return self._emit_call(node)

        if isinstance(node, Index):
            return f"{self._emit_expr(node.obj)}[{self._emit_expr(node.index)}]"

        if isinstance(node, Member):
            return f"{self._emit_expr(node.obj)}.{node.field_name}"

        if isinstance(node, Array):
            elements = ", ".join(self._emit_expr(e) for e in node.elements)
            return f"[{elements}]"

        if isinstance(node, MapLiteral):
            pairs = ", ".join(
                f"{self._emit_map_key(k)}: {self._emit_expr(v)}"
                for k, v in node.pairs
            )
            return f"{{{pairs}}}"

        if isinstance(node, Lambda):
            params = ", ".join(node.params)
            body = self._emit_expr(node.body)
            if len(node.params) == 1:
                return f"({node.params[0]}) => {body}"
            return f"({params}) => {body}"

        if isinstance(node, Conditional):
            return (f"({self._emit_expr(node.condition)} "
                    f"? {self._emit_expr(node.then_expr)} "
                    f": {self._emit_expr(node.else_expr)})")

        if isinstance(node, Range):
            start = self._emit_expr(node.start)
            end = self._emit_expr(node.end)
            if node.inclusive:
                return f"Array.from({{length: {end} - {start} + 1}}, (_, i) => i + {start})"
            return f"Array.from({{length: {end} - {start}}}, (_, i) => i + {start})"

        if isinstance(node, Pipe):
            return f"{self._emit_expr(node.right)}({self._emit_expr(node.left)})"

        if isinstance(node, StepChain):
            return self._emit_step_chain(node)

        if isinstance(node, StringInterp):
            return self._emit_string_interp(node)

        return f"/* <{type(node).__name__}> */"

    def _emit_literal(self, node: Literal) -> str:
        if node.value is None:
            return "null"
        if isinstance(node.value, bool):
            return "true" if node.value else "false"
        if isinstance(node.value, str):
            escaped = (node.value
                       .replace("\\", "\\\\")
                       .replace('"', '\\"')
                       .replace("\n", "\\n")
                       .replace("\r", "\\r")
                       .replace("\t", "\\t"))
            return f'"{escaped}"'
        return str(node.value)

    def _emit_map_key(self, node: ASTNode) -> str:
        """Emit a map key, using unquoted identifiers where possible."""
        if isinstance(node, Literal) and isinstance(node.value, str):
            # Use bracket-free key if it's a valid JS identifier
            if node.value.isidentifier():
                return node.value
            escaped = node.value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return f"[{self._emit_expr(node)}]"

    def _emit_binary(self, node: BinaryOp) -> str:
        left = self._emit_expr(node.left)
        right = self._emit_expr(node.right)
        op = node.op

        if op == "has":
            return f"{left}.includes({right})"
        if op == "hasnt":
            return f"!{left}.includes({right})"
        if op == "isin":
            return f"{right}.includes({left})"
        if op == "islike":
            return f"new RegExp({right}.replace(/\\*/g, '.*').replace(/\\?/g, '.')).test({left})"
        if op == "//":
            return f"Math.trunc({left} / {right})"

        js_op = _OP_MAP.get(op, op)
        return f"({left} {js_op} {right})"

    def _emit_unary(self, node: UnaryOp) -> str:
        operand = self._emit_expr(node.operand)
        if node.op == "not":
            return f"!{operand}"
        if node.op == "~":
            return f"~{operand}"
        return f"-{operand}"

    def _emit_call(self, node: Call) -> str:
        args_strs = [self._emit_expr(a) for a in node.args]

        if isinstance(node.callee, Identifier):
            name = node.callee.name

            if name in _BUILTIN_MAP:
                template = _BUILTIN_MAP[name]

                # Special multi-arg handling
                if name == "split":
                    if len(args_strs) == 1:
                        return f"{args_strs[0]}.split()"
                    return f"{args_strs[0]}.split({args_strs[1]})"
                if name == "join":
                    if len(args_strs) == 1:
                        return f"{args_strs[0]}.join('')"
                    return f"{args_strs[0]}.join({args_strs[1]})"
                if name == "slice":
                    if len(args_strs) == 2:
                        return f"{args_strs[0]}.slice({args_strs[1]})"
                    return f"{args_strs[0]}.slice({args_strs[1]}, {args_strs[2]})"
                if name == "contains":
                    return f"{args_strs[0]}.includes({args_strs[1]})"
                if name == "range":
                    if len(args_strs) == 1:
                        return f"Array.from({{length: {args_strs[0]}}}, (_, i) => i)"
                    if len(args_strs) == 2:
                        return f"Array.from({{length: {args_strs[1]} - {args_strs[0]}}}, (_, i) => i + {args_strs[0]})"
                    return f"Array.from({{length: Math.ceil(({args_strs[1]} - {args_strs[0]}) / {args_strs[2]})}}, (_, i) => {args_strs[0]} + i * {args_strs[2]})"
                if name == "zip":
                    return f"{args_strs[0]}.map((e, i) => [e, {args_strs[1]}[i]])"

                # Generic template substitution
                result = template
                for i, a in enumerate(args_strs):
                    result = result.replace(f"{{{i}}}", a)
                result = result.replace("{args}", ", ".join(args_strs))
                return result

            # Assert functions
            if name == "assert":
                if len(args_strs) == 1:
                    return f"console.assert({args_strs[0]})"
                return f"console.assert({args_strs[0]}, {args_strs[1]})"
            if name == "assert_equal":
                return f"console.assert({args_strs[0]} === {args_strs[1]})"
            if name == "assert_true":
                return f"console.assert({args_strs[0]})"
            if name == "assert_false":
                return f"console.assert(!{args_strs[0]})"

            # http_get
            if name == "http_get":
                return f"await fetch({args_strs[0]}).then(r => r.json())"

            # Date functions
            if name == "date_now":
                return "new Date().toISOString()"
            if name == "date_parse":
                return f"new Date({args_strs[0]}).toISOString()"
            if name == "date_format":
                return f"new Date({args_strs[0]}).toLocaleDateString()"
            if name == "date_add":
                return f"new Date(new Date({args_strs[0]}).getTime() + {args_strs[1]} * 86400000).toISOString()"
            if name == "date_diff":
                return f"(new Date({args_strs[0]}) - new Date({args_strs[1]})) / 86400000"

        # Generic function call
        callee = self._emit_expr(node.callee)
        return f"{callee}({', '.join(args_strs)})"

    def _emit_string_interp(self, node: StringInterp) -> str:
        parts = []
        for part in node.parts:
            if isinstance(part, str):
                # Escape backticks and ${} in template literals
                escaped = part.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
                parts.append(escaped)
            else:
                parts.append(f"${{{self._emit_expr(part)}}}")
        return f'`{"".join(parts)}`'

    # -------------------------------------------------------------------
    # Step chains
    # -------------------------------------------------------------------

    def _emit_step_chain(self, node: StepChain) -> str:
        result = self._emit_expr(node.source)

        for step_name, step_args in node.steps:
            args = [self._emit_expr(a) for a in step_args]
            result = self._apply_step(result, step_name, args)

        return result

    def _apply_step(self, data: str, step: str, args: list[str]) -> str:
        """Convert a single step chain operation to JavaScript."""

        if step == "_filter":
            fn = args[0] if args else "Boolean"
            return f"{data}.filter({fn})"

        if step == "_map":
            fn = args[0] if args else "(x) => x"
            return f"{data}.map({fn})"

        if step == "_sort":
            if args:
                return f"{data}.slice().sort((a, b) => {args[0]}(a) < {args[0]}(b) ? -1 : {args[0]}(a) > {args[0]}(b) ? 1 : 0)"
            return f"{data}.slice().sort((a, b) => a - b)"

        if step == "_sortBy":
            fn = args[0]
            return f"{data}.slice().sort((a, b) => {fn}(a) < {fn}(b) ? -1 : {fn}(a) > {fn}(b) ? 1 : 0)"

        if step == "_reverse":
            return f"{data}.slice().reverse()"

        if step == "_take":
            return f"{data}.slice(0, {args[0]})"

        if step == "_drop":
            return f"{data}.slice({args[0]})"

        if step == "_first":
            return f"{data}[0]"

        if step == "_last":
            return f"{data}.at(-1)"

        if step == "_unique":
            return f"[...new Set({data})]"

        if step == "_flatten":
            return f"{data}.flat()"

        if step == "_count":
            if args:
                return f"{data}.filter({args[0]}).length"
            return f"{data}.length"

        if step == "_sum":
            return f"{data}.reduce((a, b) => a + b, 0)"

        if step == "_avg":
            return f"({data}.reduce((a, b) => a + b, 0) / {data}.length)"

        if step == "_min":
            return f"Math.min(...{data})"

        if step == "_max":
            return f"Math.max(...{data})"

        if step in ("_group", "_groupBy", "_group_by"):
            fn = args[0]
            return (f"{data}.reduce((groups, item) => "
                    f"((groups[{fn}(item)] = groups[{fn}(item)] || []).push(item), groups), {{}})")

        if step == "_reduce":
            fn = args[0]
            if len(args) > 1:
                return f"{data}.reduce({fn}, {args[1]})"
            return f"{data}.reduce({fn})"

        if step == "_each":
            return f"((arr) => (arr.forEach({args[0]}), arr))({data})"

        if step == "_zip":
            return f"{data}.map((e, i) => [e, {args[0]}[i]])"

        if step == "_chunk":
            n = args[0] if args else "2"
            return (f"Array.from({{length: Math.ceil({data}.length / {n})}}, "
                    f"(_, i) => {data}.slice(i * {n}, (i + 1) * {n}))")

        if step == "_join":
            right = args[0]
            fn = args[1]
            return (f"{data}.flatMap(l => "
                    f"{right}.filter(r => {fn}(l) === {fn}(r))"
                    f".map(r => ({{...l, ...r}})))")

        if step in ("_leftJoin", "_left_join"):
            right = args[0]
            fn = args[1]
            return (f"{data}.map(l => ({{...l, "
                    f"...({right}.find(r => {fn}(r) === {fn}(l)) || {{}})}}))")

        # dplyr-style verbs
        if step == "_select":
            if len(args) == 1:
                cols = args[0]
                return f"{data}.map(row => {cols}.reduce((o, k) => (o[k] = row[k], o), {{}}))"
            cols_str = ", ".join(args)
            return f"{data}.map(row => [{cols_str}].reduce((o, k) => (o[k] = row[k], o), {{}}))"

        if step == "_mutate":
            fn = args[0]
            return f"{data}.map(row => ({{...row, ...{fn}(row)}}))"

        if step == "_summarize":
            return f"Object.fromEntries(Object.entries({args[0]}).map(([k, fn]) => [k, fn({data})]))"

        if step == "_rename":
            rename_map = args[0]
            return (f"{data}.map(row => Object.fromEntries("
                    f"Object.entries(row).map(([k, v]) => [{rename_map}[k] || k, v])))")

        if step == "_arrange":
            fn = args[0]
            if len(args) > 1:
                return f"{data}.slice().sort((a, b) => {fn}(b) < {fn}(a) ? -1 : {fn}(b) > {fn}(a) ? 1 : 0)"
            return f"{data}.slice().sort((a, b) => {fn}(a) < {fn}(b) ? -1 : {fn}(a) > {fn}(b) ? 1 : 0)"

        if step in ("_distinct", "_unique"):
            if args:
                fn = args[0]
                return f"[...new Map({data}.map(x => [{fn}(x), x])).values()]"
            return f"[...new Set({data})]"

        if step == "_slice":
            start = args[0] if args else "0"
            if len(args) > 1:
                return f"{data}.slice({start}, {start} + {args[1]})"
            return f"{data}.slice({start})"

        if step == "_pull":
            col = args[0]
            return f"{data}.map(row => row[{col}])"

        if step == "_mapValues":
            fn = args[0]
            return f"Object.fromEntries(Object.entries({data}).map(([k, v]) => [k, {fn}(v)]))"

        if step == "_pivot":
            idx_fn, col_fn, val_fn = args[0], args[1], args[2]
            return (f"{data}.reduce((acc, r) => "
                    f"((acc[{idx_fn}(r)] = acc[{idx_fn}(r)] || {{}})["
                    f"{col_fn}(r)] = {val_fn}(r), acc), {{}})")

        if step == "_unpivot":
            id_cols = args[0]
            return (f"{data}.flatMap(row => Object.entries(row)"
                    f".filter(([k]) => !{id_cols}.includes(k))"
                    f".map(([k, v]) => ({{...Object.fromEntries({id_cols}.map(c => [c, row[c]])), "
                    f"variable: k, value: v}})))")

        if step == "_window":
            n = args[0]
            fn = args[1]
            return (f"{data}.map((_, i, arr) => "
                    f"{fn}(arr.slice(Math.max(0, i - {n} + 1), i + 1)))")

        return f"/* unknown step: {step} */({data})"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def transpile_js(source: str) -> str:
    """Transpile TinyTalk source to JavaScript."""
    return JavaScriptTranspiler().transpile(source)
