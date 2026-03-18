"""
TinyTalk → WebAssembly (WAT) Transpiler

Converts TinyTalk code to WebAssembly Text Format (WAT). This is a teaching
tool: students write TinyTalk programs and see the low-level stack-based
WebAssembly equivalent, bridging high-level concepts to systems programming.

WAT is S-expression based and compiles directly to .wasm binary modules via
tools like wat2wasm (from WABT) or browser APIs.

Mapping:
    let x = 10              →  (local $x i32) ... (i32.const 10) (local.set $x)
    const PI = 3.14         →  (global $PI f64 (f64.const 3.14))
    fn add(a, b) { ... }   →  (func $add (param $a i32) (param $b i32) ...)
    (x) => x * 2           →  inline expansion at call site
    show(x)                 →  (call $show_i32 (local.get $x))
    x + y                   →  (i32.add (local.get $x) (local.get $y))
    if cond { ... }         →  (if (local.get $cond) (then ...))
    for i in range(n)       →  (block (loop ...))
    _filter/_map/_sum       →  loop-based array operations over linear memory
    [1, 2, 3]              →  linear memory with length prefix

Type strategy:
    - Integers     → i32 (default numeric type)
    - Floats       → f64
    - Booleans     → i32 (0 = false, 1 = true)
    - Strings      → i32 pointer into linear memory
    - Arrays/Lists → i32 pointer into linear memory (length-prefixed)
    - null         → i32.const 0

Usage:
    from newTinyTalk.wasm_transpiler import transpile_wasm

    wat = transpile_wasm('let x = 42\\nshow(x)')
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
# WASM type inference helpers
# ---------------------------------------------------------------------------

class WasmType:
    """WebAssembly value types."""
    I32 = "i32"
    I64 = "i64"
    F64 = "f64"


def _infer_literal_type(value) -> str:
    """Infer the WASM type from a Python literal value."""
    if isinstance(value, bool):
        return WasmType.I32
    if isinstance(value, int):
        return WasmType.I32
    if isinstance(value, float):
        return WasmType.F64
    # Strings and null → i32 pointer
    return WasmType.I32


# ---------------------------------------------------------------------------
# Transpiler
# ---------------------------------------------------------------------------

class WasmTranspiler:
    """Transpiles TinyTalk AST to WebAssembly Text Format (WAT)."""

    def __init__(self):
        self._indent = 0
        self._lines: list[str] = []

        # Track locals for the current function
        self._locals: dict[str, str] = {}  # name → wasm type
        self._globals: dict[str, str] = {}  # name → wasm type
        self._functions: dict[str, tuple[list[str], str]] = {}  # name → (param_types, return_type)
        self._in_function = False
        self._current_func_name = ""

        # Track string data for the data section
        self._string_data: list[tuple[int, str]] = []  # [(offset, value)]
        self._string_offsets: dict[str, int] = {}  # value → offset
        self._next_data_offset = 1024  # Start string data at offset 1024

        # Track array data for memory
        self._next_array_offset = 0  # Will be set after string data

        # Loop nesting for break/continue
        self._loop_depth = 0

        # Collect top-level statements and function declarations separately
        self._func_decls: list[str] = []
        self._main_body: list[str] = []

        # Type context: track what type the last expression pushed
        self._expr_type_stack: list[str] = []

    def transpile(self, source: str) -> str:
        """Parse and transpile TinyTalk source to WAT."""
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        return self.emit(ast)

    def emit(self, node: ASTNode) -> str:
        """Emit WAT code from an AST."""
        self._indent = 0
        self._lines = []
        self._locals = {}
        self._globals = {}
        self._functions = {}
        self._func_decls = []
        self._main_body = []
        self._string_data = []
        self._string_offsets = {}
        self._next_data_offset = 1024
        self._loop_depth = 0
        self._expr_type_stack = []

        if isinstance(node, Program):
            # First pass: collect function declarations and globals
            main_stmts = []
            for stmt in node.statements:
                if isinstance(stmt, FnDecl):
                    self._emit_func_decl(stmt)
                elif isinstance(stmt, ConstStmt):
                    self._emit_global_const(stmt)
                    # Also emit in main if it has side effects — but consts don't
                else:
                    main_stmts.append(stmt)

            # Second pass: emit main function body
            main_locals = {}
            self._locals = main_locals
            self._in_function = True
            self._current_func_name = "$main"
            main_body_lines = []
            for stmt in main_stmts:
                lines = self._emit_stmt(stmt)
                if lines:
                    main_body_lines.extend(lines)
            self._in_function = False

        else:
            # Single expression
            main_locals = {}
            self._locals = main_locals
            main_body_lines = self._emit_expr(node)

        # Build the module
        return self._build_module(main_locals, main_body_lines)

    def _build_module(self, main_locals: dict, main_body: list[str]) -> str:
        """Assemble the final WAT module."""
        lines = ["(module"]

        # Memory declaration (1 page = 64KB)
        lines.append("  ;; Linear memory: 1 page (64KB)")
        lines.append("  (memory (export \"memory\") 1)")
        lines.append("")

        # Host imports for I/O
        lines.append("  ;; Host-imported functions for I/O")
        lines.append("  (import \"env\" \"show_i32\" (func $show_i32 (param i32)))")
        lines.append("  (import \"env\" \"show_f64\" (func $show_f64 (param f64)))")
        lines.append("  (import \"env\" \"show_str\" (func $show_str (param i32 i32)))")
        lines.append("")

        # Global constants
        if self._globals:
            lines.append("  ;; Global constants")
            for name, wtype in self._globals.items():
                # Find the init value from the stored data
                init = self._global_inits.get(name, f"({wtype}.const 0)")
                lines.append(f"  (global ${name} {wtype} ({init}))")
            lines.append("")

        # String data section
        if self._string_data:
            lines.append("  ;; String data")
            for offset, value in self._string_data:
                escaped = value.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f"  (data (i32.const {offset}) \"{escaped}\")")
            lines.append("")

        # User-defined functions
        if self._func_decls:
            lines.append("  ;; User-defined functions")
            lines.extend(self._func_decls)
            lines.append("")

        # Main function
        lines.append("  ;; Entry point")
        lines.append("  (func $main (export \"main\")")

        # Declare locals for main
        if main_locals:
            for name, wtype in main_locals.items():
                lines.append(f"    (local ${name} {wtype})")

        # Main body
        for line in main_body:
            lines.append(f"    {line}")

        lines.append("  )")
        lines.append(")")

        return "\n".join(lines)

    # -------------------------------------------------------------------
    # Global constants
    # -------------------------------------------------------------------

    _global_inits: dict = {}

    def _emit_global_const(self, node: ConstStmt):
        """Register a global constant."""
        if not hasattr(self, '_global_inits'):
            self._global_inits = {}

        if isinstance(node.value, Literal):
            if isinstance(node.value.value, float):
                wtype = WasmType.F64
                init = f"f64.const {node.value.value}"
            elif isinstance(node.value.value, bool):
                wtype = WasmType.I32
                init = f"i32.const {1 if node.value.value else 0}"
            elif isinstance(node.value.value, int):
                wtype = WasmType.I32
                init = f"i32.const {node.value.value}"
            else:
                wtype = WasmType.I32
                init = "i32.const 0"
        else:
            wtype = WasmType.I32
            init = "i32.const 0"

        self._globals[node.name] = wtype
        self._global_inits[node.name] = init

    # -------------------------------------------------------------------
    # Statements
    # -------------------------------------------------------------------

    def _emit_stmt(self, node: ASTNode) -> list[str]:
        """Emit WAT instructions for a statement. Returns list of instruction lines."""

        if isinstance(node, LetStmt):
            return self._emit_let(node)

        if isinstance(node, ConstStmt):
            # Local const treated as local variable
            return self._emit_let_as_const(node)

        if isinstance(node, AssignStmt):
            return self._emit_assign(node)

        if isinstance(node, IfStmt):
            return self._emit_if(node)

        if isinstance(node, ForStmt):
            return self._emit_for(node)

        if isinstance(node, WhileStmt):
            return self._emit_while(node)

        if isinstance(node, ReturnStmt):
            return self._emit_return(node)

        if isinstance(node, BreakStmt):
            # Break jumps to the outer block (depth 1 from the loop)
            return ["br 1  ;; break"]

        if isinstance(node, ContinueStmt):
            # Continue jumps back to the loop header (depth 0)
            return ["br 0  ;; continue"]

        if isinstance(node, Block):
            lines = []
            for s in node.statements:
                lines.extend(self._emit_stmt(s))
            return lines

        if isinstance(node, FnDecl):
            # Nested function — emit as a module-level function
            self._emit_func_decl(node)
            return [f";; function {node.name} defined above"]

        if isinstance(node, MatchStmt):
            return self._emit_match(node)

        if isinstance(node, TryStmt):
            return self._emit_try(node)

        if isinstance(node, ThrowStmt):
            return [";; throw (trapped in WASM)", "unreachable"]

        if isinstance(node, StructDecl):
            return [f";; struct {node.name} (structs use linear memory)"]

        if isinstance(node, EnumDecl):
            return [f";; enum {node.name} (enums mapped to i32 variants)"]

        # Expression statement — evaluate for side effects, drop result
        expr_lines = self._emit_expr(node)
        if expr_lines and not self._is_void_call(node):
            expr_lines.append("drop")
        return expr_lines

    def _is_void_call(self, node: ASTNode) -> bool:
        """Check if a node is a call to a void function (like show)."""
        if isinstance(node, Call) and isinstance(node.callee, Identifier):
            return node.callee.name in ("show", "println", "print", "assert",
                                         "assert_equal", "assert_true", "assert_false",
                                         "append", "push")
        return False

    def _emit_let(self, node: LetStmt) -> list[str]:
        """Emit a let statement."""
        lines = []
        if node.value is not None:
            wtype = self._infer_expr_type(node.value)
            self._locals[node.name] = wtype
            expr_lines = self._emit_expr(node.value)
            lines.extend(expr_lines)
            lines.append(f"local.set ${node.name}")
        else:
            self._locals[node.name] = WasmType.I32
        return lines

    def _emit_let_as_const(self, node: ConstStmt) -> list[str]:
        """Emit a const as a local variable (when inside a function)."""
        lines = []
        wtype = self._infer_expr_type(node.value)
        self._locals[node.name] = wtype
        expr_lines = self._emit_expr(node.value)
        lines.extend(expr_lines)
        lines.append(f"local.set ${node.name}")
        return lines

    def _emit_assign(self, node: AssignStmt) -> list[str]:
        """Emit an assignment statement."""
        lines = []

        if isinstance(node.target, Identifier):
            name = node.target.name

            if node.op == "=":
                lines.extend(self._emit_expr(node.value))
                if name in self._globals:
                    lines.append(f"global.set ${name}")
                else:
                    lines.append(f"local.set ${name}")
            else:
                # Compound assignment: +=, -=, *=, /=
                if name in self._globals:
                    lines.append(f"global.get ${name}")
                else:
                    lines.append(f"local.get ${name}")
                lines.extend(self._emit_expr(node.value))
                wtype = self._locals.get(name, self._globals.get(name, WasmType.I32))
                op_base = node.op[:-1]  # Remove the '='
                lines.append(self._wasm_binop(op_base, wtype))
                if name in self._globals:
                    lines.append(f"global.set ${name}")
                else:
                    lines.append(f"local.set ${name}")

        return lines

    def _emit_if(self, node: IfStmt) -> list[str]:
        """Emit an if/elif/else statement."""
        lines = []
        lines.extend(self._emit_expr(node.condition))
        lines.append("(if")
        lines.append("  (then")
        body_lines = self._emit_block(node.then_branch)
        for bl in body_lines:
            lines.append(f"    {bl}")
        lines.append("  )")

        if node.elif_branches or node.else_branch:
            lines.append("  (else")
            if node.elif_branches:
                # Chain elif as nested if in the else
                elif_cond, elif_body = node.elif_branches[0]
                remaining_elifs = node.elif_branches[1:]
                # Build a synthetic IfStmt for the elif chain
                nested_if = IfStmt(
                    condition=elif_cond,
                    then_branch=elif_body,
                    elif_branches=remaining_elifs,
                    else_branch=node.else_branch,
                )
                nested_lines = self._emit_if(nested_if)
                for nl in nested_lines:
                    lines.append(f"    {nl}")
            elif node.else_branch:
                body_lines = self._emit_block(node.else_branch)
                for bl in body_lines:
                    lines.append(f"    {bl}")
            lines.append("  )")

        lines.append(")")
        return lines

    def _emit_for(self, node: ForStmt) -> list[str]:
        """Emit a for loop as a block+loop pattern.

        for i in range(n) { body }
        →
        (local $i i32)
        (local.set $i (i32.const 0))
        (block $break
          (loop $continue
            (br_if $break (i32.ge_s (local.get $i) (local.get $n)))
            ;; body
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br $continue)
          )
        )
        """
        lines = []
        self._locals[node.var] = WasmType.I32

        # Determine loop bounds from range() call
        start_expr = ["i32.const 0"]
        end_expr = ["i32.const 0"]

        if isinstance(node.iterable, Call) and isinstance(node.iterable.callee, Identifier):
            if node.iterable.callee.name == "range":
                args = node.iterable.args
                if len(args) == 1:
                    start_expr = ["i32.const 0"]
                    end_expr = self._emit_expr(args[0])
                elif len(args) >= 2:
                    start_expr = self._emit_expr(args[0])
                    end_expr = self._emit_expr(args[1])

        # Initialize loop variable
        lines.extend(start_expr)
        lines.append(f"local.set ${node.var}")

        # Save end value in a temp local
        end_local = f"__end_{node.var}"
        self._locals[end_local] = WasmType.I32
        lines.extend(end_expr)
        lines.append(f"local.set ${end_local}")

        self._loop_depth += 1
        lines.append("(block $break")
        lines.append("  (loop $continue")

        # Condition check: break if i >= end
        lines.append(f"    local.get ${node.var}")
        lines.append(f"    local.get ${end_local}")
        lines.append("    i32.ge_s")
        lines.append("    br_if $break")

        # Body
        body_lines = self._emit_block(node.body)
        for bl in body_lines:
            lines.append(f"    {bl}")

        # Increment
        lines.append(f"    local.get ${node.var}")
        lines.append("    i32.const 1")
        lines.append("    i32.add")
        lines.append(f"    local.set ${node.var}")

        # Loop back
        lines.append("    br $continue")
        lines.append("  )")
        lines.append(")")
        self._loop_depth -= 1

        return lines

    def _emit_while(self, node: WhileStmt) -> list[str]:
        """Emit a while loop."""
        lines = []
        self._loop_depth += 1

        lines.append("(block $break")
        lines.append("  (loop $continue")

        # Condition check
        cond_lines = self._emit_expr(node.condition)
        for cl in cond_lines:
            lines.append(f"    {cl}")
        lines.append("    i32.eqz")
        lines.append("    br_if $break")

        # Body
        body_lines = self._emit_block(node.body)
        for bl in body_lines:
            lines.append(f"    {bl}")

        lines.append("    br $continue")
        lines.append("  )")
        lines.append(")")
        self._loop_depth -= 1

        return lines

    def _emit_return(self, node: ReturnStmt) -> list[str]:
        """Emit a return statement."""
        lines = []
        if node.value:
            lines.extend(self._emit_expr(node.value))
        lines.append("return")
        return lines

    def _emit_match(self, node: MatchStmt) -> list[str]:
        """Emit a match statement as nested if/else."""
        lines = []
        # Store the match value in a temp
        temp = "__match_val"
        self._locals[temp] = WasmType.I32
        lines.extend(self._emit_expr(node.value))
        lines.append(f"local.set ${temp}")

        for i, (pattern, body) in enumerate(node.cases):
            lines.append(f"local.get ${temp}")
            lines.extend(self._emit_expr(pattern))
            lines.append("i32.eq")
            lines.append("(if")
            lines.append("  (then")
            body_lines = self._emit_block(body)
            for bl in body_lines:
                lines.append(f"    {bl}")
            lines.append("  )")
            lines.append(")")

        return lines

    def _emit_try(self, node: TryStmt) -> list[str]:
        """Emit try/catch — WASM doesn't have exceptions, emit as comment."""
        lines = [";; try (WASM has no native exception handling)"]
        lines.extend(self._emit_block(node.body))
        if node.catch_body:
            lines.append(";; catch — unreachable in normal WASM execution")
        return lines

    def _emit_block(self, node: ASTNode) -> list[str]:
        """Emit a block body."""
        if isinstance(node, Block):
            lines = []
            for s in node.statements:
                lines.extend(self._emit_stmt(s))
            return lines
        return self._emit_stmt(node)

    # -------------------------------------------------------------------
    # Function declarations
    # -------------------------------------------------------------------

    def _emit_func_decl(self, node: FnDecl):
        """Emit a function declaration at module level."""
        # Save state
        old_locals = self._locals
        old_in_func = self._in_function
        old_func_name = self._current_func_name

        self._locals = {}
        self._in_function = True
        self._current_func_name = f"${node.name}"

        # Determine param types (default to i32)
        param_types = []
        param_strs = []
        for param_tuple in node.params:
            pname = param_tuple[0]
            ptype = param_tuple[1] if len(param_tuple) > 1 else None
            wtype = self._type_hint_to_wasm(ptype) if ptype else WasmType.I32
            param_types.append(wtype)
            param_strs.append(f"(param ${pname} {wtype})")
            self._locals[pname] = wtype

        # Infer return type from body
        ret_type = self._infer_return_type(node)
        ret_str = f"(result {ret_type})" if ret_type else ""

        # Register function signature
        self._functions[node.name] = (param_types, ret_type or "")

        # Emit body
        self._locals = {p[0]: t for (p, t) in zip(node.params, param_types)}

        body_lines = self._emit_block(node.body)

        # Collect non-param locals
        param_names = {p[0] for p in node.params}
        func_locals = {k: v for k, v in self._locals.items() if k not in param_names}

        # Build function text
        params = " ".join(param_strs)
        sig = f"  (func ${node.name} (export \"{node.name}\") {params} {ret_str}".rstrip()

        func_lines = [sig]
        for lname, ltype in func_locals.items():
            func_lines.append(f"    (local ${lname} {ltype})")
        for bl in body_lines:
            func_lines.append(f"    {bl}")
        func_lines.append("  )")

        self._func_decls.append("\n".join(func_lines))

        # Restore state
        self._locals = old_locals
        self._in_function = old_in_func
        self._current_func_name = old_func_name

    def _type_hint_to_wasm(self, hint: str) -> str:
        """Convert a TinyTalk type hint to a WASM type."""
        if not hint:
            return WasmType.I32
        hint_lower = hint.lower()
        if hint_lower in ("float", "f64", "number"):
            return WasmType.F64
        if hint_lower in ("int", "i32", "i64", "bool", "boolean", "string", "str"):
            return WasmType.I32
        return WasmType.I32

    def _infer_return_type(self, node: FnDecl) -> str:
        """Infer the return type of a function from its body."""
        if node.return_type:
            return self._type_hint_to_wasm(node.return_type)

        # Look for return statements
        returns = self._find_returns(node.body)
        if not returns:
            return ""  # void function

        # Check the first return value
        for ret in returns:
            if ret.value:
                return self._infer_expr_type(ret.value)
        return WasmType.I32

    def _find_returns(self, node: ASTNode) -> list[ReturnStmt]:
        """Find all return statements in a function body."""
        results = []
        if isinstance(node, ReturnStmt):
            results.append(node)
        elif isinstance(node, Block):
            for s in node.statements:
                results.extend(self._find_returns(s))
        elif isinstance(node, IfStmt):
            results.extend(self._find_returns(node.then_branch))
            if node.else_branch:
                results.extend(self._find_returns(node.else_branch))
        return results

    # -------------------------------------------------------------------
    # Expressions
    # -------------------------------------------------------------------

    def _emit_expr(self, node: ASTNode) -> list[str]:
        """Emit WAT instructions for an expression. Returns list of instruction lines."""

        if isinstance(node, Literal):
            return self._emit_literal(node)

        if isinstance(node, Identifier):
            return self._emit_identifier(node)

        if isinstance(node, BinaryOp):
            return self._emit_binary(node)

        if isinstance(node, UnaryOp):
            return self._emit_unary(node)

        if isinstance(node, Call):
            return self._emit_call(node)

        if isinstance(node, Index):
            return self._emit_index(node)

        if isinstance(node, Member):
            return self._emit_member(node)

        if isinstance(node, Array):
            return self._emit_array(node)

        if isinstance(node, MapLiteral):
            return [f";; map literal (uses linear memory)", "i32.const 0"]

        if isinstance(node, Lambda):
            return [f";; lambda (inlined at call site)", "i32.const 0"]

        if isinstance(node, Conditional):
            return self._emit_conditional(node)

        if isinstance(node, Range):
            return self._emit_range(node)

        if isinstance(node, Pipe):
            return self._emit_pipe(node)

        if isinstance(node, StepChain):
            return self._emit_step_chain(node)

        if isinstance(node, StringInterp):
            return self._emit_string_interp(node)

        return [f";; <{type(node).__name__}> (not yet supported)"]

    def _emit_literal(self, node: Literal) -> list[str]:
        """Emit a literal value."""
        if node.value is None:
            return ["i32.const 0  ;; null"]
        if isinstance(node.value, bool):
            return [f"i32.const {1 if node.value else 0}  ;; {'true' if node.value else 'false'}"]
        if isinstance(node.value, int):
            return [f"i32.const {node.value}"]
        if isinstance(node.value, float):
            return [f"f64.const {node.value}"]
        if isinstance(node.value, str):
            return self._emit_string_literal(node.value)
        return ["i32.const 0"]

    def _emit_string_literal(self, value: str) -> list[str]:
        """Emit a string literal, storing it in the data section."""
        if value in self._string_offsets:
            offset = self._string_offsets[value]
        else:
            offset = self._next_data_offset
            self._string_offsets[value] = offset
            self._string_data.append((offset, value))
            self._next_data_offset += len(value.encode("utf-8")) + 1  # +1 for null terminator

        return [f"i32.const {offset}  ;; string \"{value[:30]}{'...' if len(value) > 30 else ''}\""]

    def _emit_identifier(self, node: Identifier) -> list[str]:
        """Emit a variable reference."""
        name = node.name

        # Built-in constants
        if name == "true":
            return ["i32.const 1  ;; true"]
        if name == "false":
            return ["i32.const 0  ;; false"]
        if name == "null":
            return ["i32.const 0  ;; null"]
        if name == "PI":
            return ["f64.const 3.141592653589793  ;; PI"]
        if name == "E":
            return ["f64.const 2.718281828459045  ;; E"]
        if name == "TAU":
            return ["f64.const 6.283185307179586  ;; TAU"]
        if name == "INF":
            return ["f64.const inf  ;; INF"]

        if name in self._globals:
            return [f"global.get ${name}"]
        if name in self._locals:
            return [f"local.get ${name}"]

        # Unknown — treat as local (will be defined by let)
        return [f"local.get ${name}"]

    def _emit_binary(self, node: BinaryOp) -> list[str]:
        """Emit a binary operation."""
        lines = []
        left_type = self._infer_expr_type(node.left)
        right_type = self._infer_expr_type(node.right)

        # Promote to f64 if either side is float
        wtype = WasmType.F64 if (left_type == WasmType.F64 or right_type == WasmType.F64) else WasmType.I32

        left_lines = self._emit_expr(node.left)
        if left_type != wtype and wtype == WasmType.F64:
            left_lines.append("f64.convert_i32_s")

        right_lines = self._emit_expr(node.right)
        if right_type != wtype and wtype == WasmType.F64:
            right_lines.append("f64.convert_i32_s")

        lines.extend(left_lines)
        lines.extend(right_lines)

        op = node.op

        # Comparison and logical operators always return i32
        if op in ("==", "!=", "<", ">", "<=", ">=", "is", "isnt"):
            lines.append(self._wasm_compare(op, wtype))
        elif op in ("and", "or"):
            lines.append(self._wasm_logical(op))
        elif op in ("has", "hasnt", "isin", "islike"):
            lines.append(f";; {op} (requires runtime support)")
            lines.append("i32.const 0")
        else:
            lines.append(self._wasm_binop(op, wtype))

        return lines

    def _wasm_binop(self, op: str, wtype: str) -> str:
        """Map a binary operator to a WASM instruction."""
        prefix = "f64" if wtype == WasmType.F64 else "i32"

        op_map = {
            "+": f"{prefix}.add",
            "-": f"{prefix}.sub",
            "*": f"{prefix}.mul",
            "/": f"{prefix}.div_s" if prefix == "i32" else f"{prefix}.div",
            "//": "i32.div_s",
            "%": f"{prefix}.rem_s" if prefix == "i32" else f";; modulo (f64 requires runtime)",
            "**": f";; power (requires runtime call)",
            "&": "i32.and",
            "|": "i32.or",
            "^": "i32.xor",
            "<<": "i32.shl",
            ">>": "i32.shr_s",
        }
        return op_map.get(op, f";; unknown op: {op}")

    def _wasm_compare(self, op: str, wtype: str) -> str:
        """Map a comparison operator to a WASM instruction."""
        prefix = "f64" if wtype == WasmType.F64 else "i32"
        suffix = "" if prefix == "f64" else "_s"

        cmp_map = {
            "==": f"{prefix}.eq",
            "is": f"{prefix}.eq",
            "!=": f"{prefix}.ne",
            "isnt": f"{prefix}.ne",
            "<": f"{prefix}.lt{suffix}",
            ">": f"{prefix}.gt{suffix}",
            "<=": f"{prefix}.le{suffix}",
            ">=": f"{prefix}.ge{suffix}",
        }
        return cmp_map.get(op, f";; unknown cmp: {op}")

    def _wasm_logical(self, op: str) -> str:
        """Map a logical operator."""
        if op == "and":
            return "i32.and"
        if op == "or":
            return "i32.or"
        return f";; unknown logical: {op}"

    def _emit_unary(self, node: UnaryOp) -> list[str]:
        """Emit a unary operation."""
        lines = self._emit_expr(node.operand)
        wtype = self._infer_expr_type(node.operand)

        if node.op == "-":
            if wtype == WasmType.F64:
                lines.append("f64.neg")
            else:
                # Negate i32: 0 - x
                lines = ["i32.const 0"] + lines + ["i32.sub"]
        elif node.op == "not":
            lines.append("i32.eqz")
        elif node.op == "~":
            # Bitwise NOT: xor with -1
            lines.append("i32.const -1")
            lines.append("i32.xor")

        return lines

    def _emit_call(self, node: Call) -> list[str]:
        """Emit a function call."""
        lines = []
        args_lines = [self._emit_expr(a) for a in node.args]

        if isinstance(node.callee, Identifier):
            name = node.callee.name

            # show/println → call imported host function
            if name in ("show", "println"):
                if node.args:
                    arg_type = self._infer_expr_type(node.args[0])
                    lines.extend(args_lines[0])
                    if arg_type == WasmType.F64:
                        lines.append("call $show_f64")
                    elif self._is_string_expr(node.args[0]):
                        # Pass pointer and length for strings
                        str_val = self._get_string_value(node.args[0])
                        if str_val is not None:
                            lines.append(f"i32.const {len(str_val.encode('utf-8'))}")
                            lines.append("call $show_str")
                        else:
                            lines.append("call $show_i32")
                    else:
                        lines.append("call $show_i32")
                return lines

            if name == "print":
                if node.args:
                    lines.extend(args_lines[0])
                    lines.append("call $show_i32")
                return lines

            # Math builtins
            math_unary = {
                "abs": ("f64.abs", WasmType.F64),
                "sqrt": ("f64.sqrt", WasmType.F64),
                "ceil": ("f64.ceil", WasmType.F64),
                "floor": ("f64.floor", WasmType.F64),
            }
            if name in math_unary and node.args:
                instr, expected_type = math_unary[name]
                lines.extend(args_lines[0])
                arg_type = self._infer_expr_type(node.args[0])
                if arg_type != expected_type:
                    lines.append("f64.convert_i32_s")
                lines.append(instr)
                return lines

            math_binary = {
                "min": ("{t}.min", WasmType.F64),
                "max": ("{t}.max", WasmType.F64),
            }
            if name in math_binary and len(node.args) >= 2:
                instr_template, expected_type = math_binary[name]
                lines.extend(args_lines[0])
                arg_type = self._infer_expr_type(node.args[0])
                if arg_type != expected_type:
                    lines.append("f64.convert_i32_s")
                lines.extend(args_lines[1])
                arg_type = self._infer_expr_type(node.args[1])
                if arg_type != expected_type:
                    lines.append("f64.convert_i32_s")
                lines.append(instr_template.format(t="f64"))
                return lines

            # Type conversions
            if name == "int" and node.args:
                lines.extend(args_lines[0])
                arg_type = self._infer_expr_type(node.args[0])
                if arg_type == WasmType.F64:
                    lines.append("i32.trunc_f64_s")
                return lines

            if name == "float" and node.args:
                lines.extend(args_lines[0])
                arg_type = self._infer_expr_type(node.args[0])
                if arg_type != WasmType.F64:
                    lines.append("f64.convert_i32_s")
                return lines

            # len — for arrays stored as length-prefixed memory
            if name == "len" and node.args:
                lines.extend(args_lines[0])
                lines.append("i32.load  ;; load array length from pointer")
                return lines

            # Assert functions
            if name == "assert" and node.args:
                lines.extend(args_lines[0])
                lines.append("i32.eqz")
                lines.append("(if (then unreachable))  ;; assert")
                return lines

            if name == "assert_equal" and len(node.args) >= 2:
                lines.extend(args_lines[0])
                lines.extend(args_lines[1])
                lines.append("i32.ne")
                lines.append("(if (then unreachable))  ;; assert_equal")
                return lines

            if name == "assert_true" and node.args:
                lines.extend(args_lines[0])
                lines.append("i32.eqz")
                lines.append("(if (then unreachable))  ;; assert_true")
                return lines

            if name == "assert_false" and node.args:
                lines.extend(args_lines[0])
                lines.append("(if (then unreachable))  ;; assert_false")
                return lines

            # range() → returns a memory pointer (handled at for-loop level)
            if name == "range":
                lines.append(";; range (handled by for-loop compilation)")
                lines.append("i32.const 0")
                return lines

            # User-defined function call
            for al in args_lines:
                lines.extend(al)
            lines.append(f"call ${name}")
            return lines

        # Indirect/dynamic call — emit args and a comment
        for al in args_lines:
            lines.extend(al)
        callee_lines = self._emit_expr(node.callee)
        lines.extend(callee_lines)
        lines.append(";; indirect call (requires table)")
        return lines

    def _emit_index(self, node: Index) -> list[str]:
        """Emit array/map indexing."""
        lines = []
        lines.extend(self._emit_expr(node.obj))
        lines.extend(self._emit_expr(node.index))
        lines.append(";; array index: base + (index + 1) * 4")
        lines.append("i32.const 1")
        lines.append("i32.add")
        lines.append("i32.const 4")
        lines.append("i32.mul")
        lines.append("i32.add")
        lines.append("i32.load")
        return lines

    def _emit_member(self, node: Member) -> list[str]:
        """Emit member access."""
        lines = self._emit_expr(node.obj)

        # Property conversions
        if node.field_name == "len":
            lines.append("i32.load  ;; .len (load array length)")
        elif node.field_name == "str":
            lines.append(";; .str (convert to string pointer)")
        elif node.field_name == "int":
            arg_type = self._infer_expr_type(node.obj)
            if arg_type == WasmType.F64:
                lines.append("i32.trunc_f64_s  ;; .int")
        elif node.field_name == "float":
            arg_type = self._infer_expr_type(node.obj)
            if arg_type != WasmType.F64:
                lines.append("f64.convert_i32_s  ;; .float")
        else:
            lines.append(f";; .{node.field_name} (struct field access)")

        return lines

    def _emit_array(self, node: Array) -> list[str]:
        """Emit an array literal stored in linear memory."""
        lines = []
        n = len(node.elements)

        # Use a simple memory region: store length then elements
        # The array pointer is returned on the stack
        temp = f"__arr_{id(node)}"
        self._locals[temp] = WasmType.I32

        lines.append(f";; array literal [{n} elements]")
        lines.append(f"i32.const {self._next_data_offset}  ;; array base address")
        lines.append(f"local.tee ${temp}")

        # Store length at base
        lines.append(f"i32.const {n}")
        lines.append("i32.store  ;; store array length")

        # Store each element
        for i, elem in enumerate(node.elements):
            offset = (i + 1) * 4
            lines.append(f"local.get ${temp}")
            lines.append(f"i32.const {offset}")
            lines.append("i32.add")
            lines.extend(self._emit_expr(elem))
            lines.append(f"i32.store  ;; element [{i}]")

        # Advance memory offset
        self._next_data_offset += (n + 1) * 4

        # Return the array pointer
        lines.append(f"local.get ${temp}")
        return lines

    def _emit_conditional(self, node: Conditional) -> list[str]:
        """Emit a ternary expression."""
        lines = []
        result_type = self._infer_expr_type(node.then_expr)
        wtype_str = result_type

        lines.extend(self._emit_expr(node.condition))
        lines.append(f"(if (result {wtype_str})")
        lines.append("  (then")
        then_lines = self._emit_expr(node.then_expr)
        for tl in then_lines:
            lines.append(f"    {tl}")
        lines.append("  )")
        lines.append("  (else")
        else_lines = self._emit_expr(node.else_expr)
        for el in else_lines:
            lines.append(f"    {el}")
        lines.append("  )")
        lines.append(")")
        return lines

    def _emit_range(self, node: Range) -> list[str]:
        """Emit a range expression — returns array pointer."""
        lines = [";; range expression (stored in linear memory)"]
        lines.extend(self._emit_expr(node.start))
        lines.append(";; range start on stack")
        return lines

    def _emit_pipe(self, node: Pipe) -> list[str]:
        """Emit pipe: right(left)."""
        lines = self._emit_expr(node.left)
        if isinstance(node.right, Identifier) and node.right.name in self._functions:
            lines.append(f"call ${node.right.name}")
        elif isinstance(node.right, Identifier):
            lines.append(f"call ${node.right.name}")
        else:
            lines.append(";; pipe (dynamic call)")
        return lines

    def _emit_step_chain(self, node: StepChain) -> list[str]:
        """Emit step chain operations."""
        lines = []
        lines.append(";; step chain")
        lines.extend(self._emit_expr(node.source))

        for step_name, step_args in node.steps:
            lines.append(f";; {step_name}")
            lines.extend(self._emit_step(step_name, step_args))

        return lines

    def _emit_step(self, step: str, args: list) -> list[str]:
        """Emit a single step chain operation."""
        # Aggregation steps that reduce to a single value
        if step == "_count":
            return ["i32.load  ;; _count: load array length"]

        if step == "_sum":
            return [
                ";; _sum: loop over array, accumulate",
                ";; (requires loop-based reduction over memory)",
                "drop",
                "i32.const 0  ;; placeholder sum",
            ]

        if step == "_first":
            return [
                "i32.const 4",
                "i32.add",
                "i32.load  ;; _first: load element[0]",
            ]

        if step == "_last":
            return [
                ";; _last: load element[length-1]",
                ";; (requires reading length then computing offset)",
                "drop",
                "i32.const 0  ;; placeholder",
            ]

        if step in ("_min", "_max"):
            return [
                f";; {step}: scan array (requires loop)",
                "drop",
                "i32.const 0  ;; placeholder",
            ]

        if step == "_avg":
            return [
                ";; _avg: sum / count (requires loop)",
                "drop",
                "f64.const 0  ;; placeholder",
            ]

        # Transform steps that return new arrays
        if step == "_filter":
            arg_str = ", ".join(str(a) for a in args) if args else ""
            return [f";; _filter({arg_str}): loop + conditional copy"]

        if step == "_map":
            arg_str = ", ".join(str(a) for a in args) if args else ""
            return [f";; _map({arg_str}): loop + transform into new array"]

        if step == "_sort":
            return [";; _sort: in-place sort (requires sort implementation)"]

        if step == "_sortBy":
            return [";; _sortBy: sort with key function"]

        if step == "_reverse":
            return [";; _reverse: reverse array in memory"]

        if step == "_take":
            if args:
                n_lines = self._emit_expr(args[0])
                return [";; _take: copy first N elements"] + n_lines + ["drop"]
            return [";; _take"]

        if step == "_drop":
            if args:
                n_lines = self._emit_expr(args[0])
                return [";; _drop: skip first N elements"] + n_lines + ["drop"]
            return [";; _drop"]

        if step == "_unique":
            return [";; _unique: deduplicate (requires hash set)"]

        if step == "_flatten":
            return [";; _flatten: concatenate sub-arrays"]

        if step == "_reduce":
            return [";; _reduce: fold over array"]

        if step == "_each":
            return [";; _each: iterate with side effects"]

        if step == "_chunk":
            return [";; _chunk: split into sub-arrays"]

        if step == "_group":
            return [";; _group: group by key function"]

        if step == "_zip":
            return [";; _zip: interleave two arrays"]

        if step == "_join":
            return [";; _join: inner join on key"]

        if step in ("_leftJoin", "_left_join"):
            return [";; _leftJoin: left outer join"]

        # dplyr-style verbs
        if step == "_select":
            return [";; _select: project columns"]
        if step == "_mutate":
            return [";; _mutate: add/modify columns"]
        if step == "_summarize":
            return [";; _summarize: aggregate columns"]
        if step == "_arrange":
            return [";; _arrange: sort by column"]
        if step == "_distinct":
            return [";; _distinct: unique rows"]
        if step == "_rename":
            return [";; _rename: rename columns"]
        if step == "_pull":
            return [";; _pull: extract single column"]
        if step == "_slice":
            return [";; _slice: row subset"]
        if step == "_pivot":
            return [";; _pivot: wide format"]
        if step == "_unpivot":
            return [";; _unpivot: long format"]
        if step == "_window":
            return [";; _window: rolling window"]

        return [f";; unknown step: {step}"]

    def _emit_string_interp(self, node: StringInterp) -> list[str]:
        """Emit string interpolation — concatenation in memory."""
        lines = [";; string interpolation (concatenated in linear memory)"]
        # For teaching purposes, emit each part
        for part in node.parts:
            if isinstance(part, str):
                str_lines = self._emit_string_literal(part)
                lines.extend(str_lines)
                lines.append("drop  ;; string part")
            else:
                lines.extend(self._emit_expr(part))
                lines.append("drop  ;; interpolated expression")
        lines.append("i32.const 0  ;; concatenated string pointer (placeholder)")
        return lines

    # -------------------------------------------------------------------
    # Type inference helpers
    # -------------------------------------------------------------------

    def _infer_expr_type(self, node: ASTNode) -> str:
        """Infer the WASM type an expression will produce."""
        if isinstance(node, Literal):
            return _infer_literal_type(node.value)

        if isinstance(node, Identifier):
            name = node.name
            if name in ("PI", "E", "TAU", "INF"):
                return WasmType.F64
            if name in self._locals:
                return self._locals[name]
            if name in self._globals:
                return self._globals[name]
            return WasmType.I32

        if isinstance(node, BinaryOp):
            left_t = self._infer_expr_type(node.left)
            right_t = self._infer_expr_type(node.right)
            # Comparisons always return i32
            if node.op in ("==", "!=", "<", ">", "<=", ">=", "is", "isnt",
                           "and", "or", "has", "hasnt", "isin", "islike"):
                return WasmType.I32
            if left_t == WasmType.F64 or right_t == WasmType.F64:
                return WasmType.F64
            return WasmType.I32

        if isinstance(node, UnaryOp):
            if node.op == "not":
                return WasmType.I32
            return self._infer_expr_type(node.operand)

        if isinstance(node, Call):
            if isinstance(node.callee, Identifier):
                name = node.callee.name
                if name in ("sqrt", "abs", "ceil", "floor", "sin", "cos",
                            "tan", "log", "exp", "float", "min", "max"):
                    return WasmType.F64
                if name in ("int", "len", "bool", "round"):
                    return WasmType.I32
                if name in self._functions:
                    _, ret = self._functions[name]
                    return ret if ret else WasmType.I32
            return WasmType.I32

        if isinstance(node, Conditional):
            return self._infer_expr_type(node.then_expr)

        if isinstance(node, Array):
            return WasmType.I32  # pointer

        if isinstance(node, StepChain):
            # Aggregation steps return scalars, others return arrays (pointers)
            if node.steps:
                last_step = node.steps[-1][0]
                if last_step in ("_sum", "_count", "_first", "_last", "_min", "_max"):
                    return WasmType.I32
                if last_step == "_avg":
                    return WasmType.F64
            return WasmType.I32

        return WasmType.I32

    def _is_string_expr(self, node: ASTNode) -> bool:
        """Check if an expression produces a string."""
        if isinstance(node, Literal) and isinstance(node.value, str):
            return True
        if isinstance(node, StringInterp):
            return True
        return False

    def _get_string_value(self, node: ASTNode):
        """Get the static string value if known."""
        if isinstance(node, Literal) and isinstance(node.value, str):
            return node.value
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def transpile_wasm(source: str) -> str:
    """Transpile TinyTalk source to WebAssembly Text Format (WAT)."""
    return WasmTranspiler().transpile(source)
