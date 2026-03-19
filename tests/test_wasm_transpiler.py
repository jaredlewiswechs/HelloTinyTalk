"""
Tests for the TinyTalk -> WebAssembly (WAT) transpiler.
Validates that correct WAT structure and instructions are generated.
"""

import pytest

from newTinyTalk import transpile_wasm


# ---------------------------------------------------------------------------
# Module structure
# ---------------------------------------------------------------------------

class TestWasmModuleStructure:
    def test_module_wrapper(self):
        wat = transpile_wasm("let x = 1")
        assert wat.startswith("(module")
        assert wat.rstrip().endswith(")")

    def test_memory_declaration(self):
        wat = transpile_wasm("let x = 1")
        assert '(memory (export "memory") 1)' in wat

    def test_host_imports(self):
        wat = transpile_wasm("show(42)")
        assert '(import "env" "show_i32"' in wat
        assert '(import "env" "show_f64"' in wat
        assert '(import "env" "show_str"' in wat

    def test_main_export(self):
        wat = transpile_wasm("let x = 1")
        assert '(func $main (export "main")' in wat

    def test_empty_program(self):
        wat = transpile_wasm("")
        assert "(module" in wat
        assert "$main" in wat


# ---------------------------------------------------------------------------
# Literals
# ---------------------------------------------------------------------------

class TestWasmLiterals:
    def test_integer(self):
        wat = transpile_wasm("show(42)")
        assert "i32.const 42" in wat

    def test_negative_integer(self):
        wat = transpile_wasm("show(-5)")
        assert "i32.const 5" in wat
        assert "i32.sub" in wat

    def test_float(self):
        wat = transpile_wasm("show(3.14)")
        assert "f64.const 3.14" in wat

    def test_boolean_true(self):
        wat = transpile_wasm("let x = true")
        assert "i32.const 1" in wat

    def test_boolean_false(self):
        wat = transpile_wasm("let x = false")
        assert "i32.const 0" in wat

    def test_null(self):
        wat = transpile_wasm("let x = null")
        assert "i32.const 0" in wat
        assert "null" in wat

    def test_string(self):
        wat = transpile_wasm('show("hello")')
        assert "(data" in wat
        assert "hello" in wat
        assert "show_str" in wat


# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

class TestWasmVariables:
    def test_let_declaration(self):
        wat = transpile_wasm("let x = 10")
        assert "(local $x i32)" in wat
        assert "i32.const 10" in wat
        assert "local.set $x" in wat

    def test_let_float(self):
        wat = transpile_wasm("let x = 3.14")
        assert "(local $x f64)" in wat
        assert "f64.const 3.14" in wat
        assert "local.set $x" in wat

    def test_const_global(self):
        wat = transpile_wasm("const MAX = 100\nshow(MAX)")
        assert "global" in wat
        assert "100" in wat

    def test_variable_read(self):
        wat = transpile_wasm("let x = 10\nshow(x)")
        assert "local.get $x" in wat
        assert "call $show_i32" in wat

    def test_assignment(self):
        wat = transpile_wasm("let x = 0\nx = 5")
        assert "local.set $x" in wat
        assert "i32.const 5" in wat

    def test_compound_assignment(self):
        wat = transpile_wasm("let x = 10\nx += 5")
        assert "local.get $x" in wat
        assert "i32.const 5" in wat
        assert "i32.add" in wat
        assert "local.set $x" in wat


# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------

class TestWasmArithmetic:
    def test_addition(self):
        wat = transpile_wasm("show(2 + 3)")
        assert "i32.const 2" in wat
        assert "i32.const 3" in wat
        assert "i32.add" in wat

    def test_subtraction(self):
        wat = transpile_wasm("show(10 - 4)")
        assert "i32.sub" in wat

    def test_multiplication(self):
        wat = transpile_wasm("show(3 * 7)")
        assert "i32.mul" in wat

    def test_division(self):
        wat = transpile_wasm("show(10 / 2)")
        assert "i32.div_s" in wat

    def test_integer_division(self):
        wat = transpile_wasm("show(7 // 2)")
        assert "i32.div_s" in wat

    def test_modulo(self):
        wat = transpile_wasm("show(10 % 3)")
        assert "i32.rem_s" in wat

    def test_float_arithmetic(self):
        wat = transpile_wasm("show(1.5 + 2.5)")
        assert "f64.const 1.5" in wat
        assert "f64.const 2.5" in wat
        assert "f64.add" in wat

    def test_mixed_type_promotion(self):
        wat = transpile_wasm("let x = 1 + 2.5")
        assert "f64.convert_i32_s" in wat
        assert "f64.add" in wat

    def test_bitwise_and(self):
        wat = transpile_wasm("show(5 & 3)")
        assert "i32.and" in wat

    def test_bitwise_or(self):
        wat = transpile_wasm("show(5 | 3)")
        assert "i32.or" in wat

    def test_bitwise_xor(self):
        wat = transpile_wasm("show(5 ^ 3)")
        assert "i32.xor" in wat

    def test_shift_left(self):
        wat = transpile_wasm("show(1 << 3)")
        assert "i32.shl" in wat

    def test_shift_right(self):
        wat = transpile_wasm("show(8 >> 2)")
        assert "i32.shr_s" in wat


# ---------------------------------------------------------------------------
# Comparisons
# ---------------------------------------------------------------------------

class TestWasmComparisons:
    def test_equal(self):
        wat = transpile_wasm("show(5 == 5)")
        assert "i32.eq" in wat

    def test_not_equal(self):
        wat = transpile_wasm("show(5 != 3)")
        assert "i32.ne" in wat

    def test_less_than(self):
        wat = transpile_wasm("show(3 < 5)")
        assert "i32.lt_s" in wat

    def test_greater_than(self):
        wat = transpile_wasm("show(5 > 3)")
        assert "i32.gt_s" in wat

    def test_less_equal(self):
        wat = transpile_wasm("show(3 <= 5)")
        assert "i32.le_s" in wat

    def test_greater_equal(self):
        wat = transpile_wasm("show(5 >= 3)")
        assert "i32.ge_s" in wat

    def test_is_operator(self):
        wat = transpile_wasm("show(5 is 5)")
        assert "i32.eq" in wat

    def test_isnt_operator(self):
        wat = transpile_wasm("show(5 isnt 3)")
        assert "i32.ne" in wat

    def test_float_comparison(self):
        wat = transpile_wasm("show(1.5 < 2.5)")
        assert "f64.lt" in wat

    def test_logical_and(self):
        wat = transpile_wasm("show(true and false)")
        assert "i32.and" in wat

    def test_logical_or(self):
        wat = transpile_wasm("show(true or false)")
        assert "i32.or" in wat

    def test_logical_not(self):
        wat = transpile_wasm("show(not true)")
        assert "i32.eqz" in wat


# ---------------------------------------------------------------------------
# Control flow
# ---------------------------------------------------------------------------

class TestWasmControlFlow:
    def test_if_statement(self):
        wat = transpile_wasm('if true { show(1) }')
        assert "(if" in wat
        assert "(then" in wat

    def test_if_else(self):
        wat = transpile_wasm('if true { show(1) } else { show(2) }')
        assert "(if" in wat
        assert "(then" in wat
        assert "(else" in wat

    def test_for_loop(self):
        wat = transpile_wasm("for i in range(10) { show(i) }")
        assert "(block $break" in wat
        assert "(loop $continue" in wat
        assert "i32.ge_s" in wat
        assert "br_if $break" in wat
        assert "br $continue" in wat

    def test_for_loop_variable(self):
        wat = transpile_wasm("for i in range(5) { show(i) }")
        assert "(local $i i32)" in wat
        assert "local.set $i" in wat
        assert "local.get $i" in wat

    def test_while_loop(self):
        wat = transpile_wasm("let x = 0\nwhile x < 10 { x += 1 }")
        assert "(block $break" in wat
        assert "(loop $continue" in wat
        assert "i32.eqz" in wat
        assert "br_if $break" in wat

    def test_break(self):
        wat = transpile_wasm("for i in range(10) { if i == 5 { break } }")
        assert "br 1  ;; break" in wat

    def test_continue(self):
        wat = transpile_wasm("for i in range(10) { if i == 5 { continue } }")
        assert "br 0  ;; continue" in wat

    def test_ternary(self):
        wat = transpile_wasm("let x = true ? 1 : 0")
        assert "(if (result i32)" in wat
        assert "(then" in wat
        assert "(else" in wat

    def test_match(self):
        wat = transpile_wasm("let x = 1\nmatch x { 1 => show(1) 2 => show(2) }")
        assert "local.set $__match_val" in wat
        assert "i32.eq" in wat


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

class TestWasmFunctions:
    def test_function_declaration(self):
        wat = transpile_wasm("fn add(a, b) { return a + b }")
        assert "(func $add" in wat
        assert "(param $a i32)" in wat
        assert "(param $b i32)" in wat
        assert "(result i32)" in wat
        assert "i32.add" in wat

    def test_function_export(self):
        wat = transpile_wasm("fn double(x) { return x * 2 }")
        assert '(export "double")' in wat

    def test_function_call(self):
        wat = transpile_wasm("fn double(x) { return x * 2 }\nshow(double(21))")
        assert "call $double" in wat

    def test_function_return(self):
        wat = transpile_wasm("fn id(x) { return x }")
        assert "return" in wat

    def test_void_function(self):
        wat = transpile_wasm("fn greet() { show(42) }")
        assert "(func $greet" in wat
        assert "call $show_i32" in wat


# ---------------------------------------------------------------------------
# Built-in functions
# ---------------------------------------------------------------------------

class TestWasmBuiltins:
    def test_show_int(self):
        wat = transpile_wasm("show(42)")
        assert "i32.const 42" in wat
        assert "call $show_i32" in wat

    def test_show_float(self):
        wat = transpile_wasm("show(3.14)")
        assert "f64.const 3.14" in wat
        assert "call $show_f64" in wat

    def test_show_string(self):
        wat = transpile_wasm('show("hello")')
        assert "call $show_str" in wat

    def test_sqrt(self):
        wat = transpile_wasm("show(sqrt(16.0))")
        assert "f64.sqrt" in wat

    def test_abs(self):
        wat = transpile_wasm("show(abs(-5.0))")
        assert "f64.abs" in wat

    def test_floor(self):
        wat = transpile_wasm("show(floor(3.7))")
        assert "f64.floor" in wat

    def test_ceil(self):
        wat = transpile_wasm("show(ceil(3.2))")
        assert "f64.ceil" in wat

    def test_int_conversion(self):
        wat = transpile_wasm("show(int(3.14))")
        assert "i32.trunc_f64_s" in wat

    def test_float_conversion(self):
        wat = transpile_wasm("show(float(42))")
        assert "f64.convert_i32_s" in wat

    def test_len(self):
        wat = transpile_wasm("show(len([1,2,3]))")
        assert "i32.load" in wat

    def test_min(self):
        wat = transpile_wasm("show(min(3, 5))")
        assert "f64.min" in wat

    def test_max(self):
        wat = transpile_wasm("show(max(3, 5))")
        assert "f64.max" in wat

    def test_assert(self):
        wat = transpile_wasm("assert(true)")
        assert "i32.eqz" in wat
        assert "unreachable" in wat

    def test_assert_equal(self):
        wat = transpile_wasm("assert_equal(1, 1)")
        assert "i32.ne" in wat
        assert "unreachable" in wat


# ---------------------------------------------------------------------------
# Arrays
# ---------------------------------------------------------------------------

class TestWasmArrays:
    def test_array_literal(self):
        wat = transpile_wasm("let a = [1, 2, 3]")
        assert "array literal [3 elements]" in wat
        assert "i32.store" in wat

    def test_array_length_stored(self):
        wat = transpile_wasm("let a = [10, 20, 30]")
        assert "i32.const 3" in wat
        assert "i32.store  ;; store array length" in wat

    def test_array_element_access(self):
        wat = transpile_wasm("let a = [1, 2, 3]\nshow(a[0])")
        assert "i32.load" in wat


# ---------------------------------------------------------------------------
# Step chains
# ---------------------------------------------------------------------------

class TestWasmStepChains:
    def test_filter(self):
        wat = transpile_wasm("let r = [1,2,3,4,5].filter((x) => x > 2)")
        assert "filter" in wat

    def test_map(self):
        wat = transpile_wasm("let r = [1,2,3].map((x) => x * 2)")
        assert "map" in wat

    def test_sort(self):
        wat = transpile_wasm("let r = [3,1,2].sort")
        assert "sort" in wat

    def test_count(self):
        wat = transpile_wasm("let r = [1,2,3].count")
        assert "i32.load" in wat
        assert "count" in wat

    def test_sum(self):
        wat = transpile_wasm("let r = [1,2,3].sum")
        assert "sum" in wat

    def test_first(self):
        wat = transpile_wasm("let r = [1,2,3].first")
        assert "first" in wat
        assert "i32.load" in wat

    def test_take(self):
        wat = transpile_wasm("let r = [1,2,3,4,5].take(3)")
        assert "take" in wat

    def test_drop(self):
        wat = transpile_wasm("let r = [1,2,3,4,5].drop(2)")
        assert "drop" in wat

    def test_reverse(self):
        wat = transpile_wasm("let r = [1,2,3].reverse")
        assert "reverse" in wat

    def test_unique(self):
        wat = transpile_wasm("let r = [1,1,2,2,3].unique")
        assert "unique" in wat

    def test_flatten(self):
        wat = transpile_wasm("let r = [[1,2],[3,4]].flatten")
        assert "flatten" in wat

    def test_reduce(self):
        wat = transpile_wasm("let r = [1,2,3,4].reduce((a, b) => a + b, 0)")
        assert "reduce" in wat

    def test_chain_multiple(self):
        wat = transpile_wasm("let r = data.filter((x) => x > 0).sort.take(5)")
        assert "filter" in wat
        assert "sort" in wat
        assert "take" in wat
        assert "step chain" in wat

    def test_dplyr_select(self):
        wat = transpile_wasm('data.select(["name", "age"])')
        assert "select" in wat

    def test_dplyr_mutate(self):
        wat = transpile_wasm('data.mutate((r) => {"doubled": r["x"] * 2})')
        assert "mutate" in wat

    def test_dplyr_arrange(self):
        wat = transpile_wasm('data.arrange((r) => r["age"])')
        assert "arrange" in wat

    def test_pivot(self):
        wat = transpile_wasm('data.pivot((r) => r["k1"], (r) => r["k2"], (r) => r["v"])')
        assert "pivot" in wat

    def test_unpivot(self):
        wat = transpile_wasm('data.unpivot(["id"])')
        assert "unpivot" in wat

    def test_window(self):
        wat = transpile_wasm("data.window(3, (w) => w)")
        assert "window" in wat


# ---------------------------------------------------------------------------
# Math constants
# ---------------------------------------------------------------------------

class TestWasmConstants:
    def test_pi(self):
        wat = transpile_wasm("show(PI)")
        assert "f64.const 3.141592653589793" in wat

    def test_e(self):
        wat = transpile_wasm("show(E)")
        assert "f64.const 2.718281828459045" in wat

    def test_tau(self):
        wat = transpile_wasm("show(TAU)")
        assert "f64.const 6.283185307179586" in wat


# ---------------------------------------------------------------------------
# String interpolation
# ---------------------------------------------------------------------------

class TestWasmStringInterp:
    def test_string_interpolation(self):
        wat = transpile_wasm('let name = "world"\nshow("hello {name}")')
        assert "string interpolation" in wat


# ---------------------------------------------------------------------------
# Unary operators
# ---------------------------------------------------------------------------

class TestWasmUnaryOps:
    def test_negation(self):
        wat = transpile_wasm("show(-42)")
        assert "i32.const 0" in wat
        assert "i32.const 42" in wat
        assert "i32.sub" in wat

    def test_float_negation(self):
        wat = transpile_wasm("show(-3.14)")
        assert "f64.neg" in wat

    def test_not(self):
        wat = transpile_wasm("show(not true)")
        assert "i32.eqz" in wat

    def test_bitwise_not(self):
        wat = transpile_wasm("show(~5)")
        assert "i32.const -1" in wat
        assert "i32.xor" in wat


# ---------------------------------------------------------------------------
# Try/catch and throw
# ---------------------------------------------------------------------------

class TestWasmErrorHandling:
    def test_try_catch(self):
        wat = transpile_wasm('try { show(1) } catch(e) { show(2) }')
        assert "try" in wat

    def test_throw(self):
        wat = transpile_wasm('throw "error"')
        assert "unreachable" in wat


# ---------------------------------------------------------------------------
# Structs and enums
# ---------------------------------------------------------------------------

class TestWasmStructsEnums:
    def test_struct_comment(self):
        wat = transpile_wasm("struct Point { x: int, y: int }")
        assert "struct Point" in wat

    def test_enum_comment(self):
        wat = transpile_wasm("enum Color { Red, Green, Blue }")
        assert "enum Color" in wat


# ---------------------------------------------------------------------------
# Pipe operator
# ---------------------------------------------------------------------------

class TestWasmPipe:
    def test_pipe(self):
        wat = transpile_wasm("fn double(x) { return x * 2 }\nlet r = 21 |> double")
        assert "call $double" in wat


# ---------------------------------------------------------------------------
# Complex programs
# ---------------------------------------------------------------------------

class TestWasmComplexPrograms:
    def test_fibonacci(self):
        wat = transpile_wasm("""
fn fib(n) {
    if n <= 1 { return n }
    return fib(n - 1) + fib(n - 2)
}
show(fib(10))
""")
        assert "(func $fib" in wat
        assert "call $fib" in wat
        assert "(result i32)" in wat
        assert "i32.add" in wat

    def test_factorial_loop(self):
        wat = transpile_wasm("""
let result = 1
for i in range(1, 6) {
    result = result * i
}
show(result)
""")
        assert "(local $result i32)" in wat
        assert "(block $break" in wat
        assert "(loop $continue" in wat
        assert "i32.mul" in wat

    def test_multiple_functions(self):
        wat = transpile_wasm("""
fn add(a, b) { return a + b }
fn mul(a, b) { return a * b }
show(add(2, 3))
show(mul(4, 5))
""")
        assert "(func $add" in wat
        assert "(func $mul" in wat
        assert "call $add" in wat
        assert "call $mul" in wat
