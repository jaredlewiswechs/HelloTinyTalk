#!/usr/bin/env python3
"""
TinyTalk Comprehensive Stress Test
Tests every feature documented in GUIDE.md — no pytest, just raw execution.

Runs each feature as a standalone TinyTalk program via the kernel,
validates output/success, and reports results.

Run from the parent directory:
    cd /home/user && python -m newTinyTalk.stress_test
Or:
    python -c "exec(open('HelloTinyTalk/stress_test.py').read())"
"""

import sys
import os

# CRITICAL: Remove the package directory from sys.path BEFORE any stdlib imports.
# The local types.py shadows Python's stdlib types module otherwise.
_this_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_this_dir)
# Remove the package dir (it gets auto-added when running a script)
sys.path[:] = [p for p in sys.path if os.path.abspath(p) != _this_dir]
# Ensure parent is in path so the package is importable
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Create symlink (HelloTinyTalk -> newTinyTalk) if needed
symlink_path = os.path.join(_parent_dir, "newTinyTalk")
if not os.path.exists(symlink_path):
    os.symlink(_this_dir, symlink_path)

import time
import traceback

from newTinyTalk import TinyTalkKernel, transpile, transpile_pandas, transpile_sql

# ── Test infrastructure ──────────────────────────────────────────────

passed = 0
failed = 0
errors = []
kernel = TinyTalkKernel()


def run_test(name: str, code: str, *, expect_output=None, expect_contains=None,
             expect_success=True, expect_fail=False):
    """Run a TinyTalk snippet and check the result."""
    global passed, failed
    try:
        result = kernel.run(code)
        ok = True
        reason = ""

        if expect_fail:
            if result.success:
                ok = False
                reason = "Expected failure but succeeded"
        else:
            if not result.success and expect_success:
                ok = False
                reason = f"Runtime error: {result.error}"
            elif expect_output is not None:
                actual = result.output.rstrip("\n")
                expected = expect_output.rstrip("\n")
                if actual != expected:
                    ok = False
                    reason = f"Expected output {expected!r}, got {actual!r}"
            elif expect_contains is not None:
                if isinstance(expect_contains, str):
                    expect_contains = [expect_contains]
                for substr in expect_contains:
                    if substr not in result.output:
                        ok = False
                        reason = f"Output missing {substr!r}. Got: {result.output.rstrip()!r}"
                        break

        if ok:
            passed += 1
            print(f"  PASS  {name}")
        else:
            failed += 1
            errors.append((name, reason))
            print(f"  FAIL  {name}: {reason}")

    except Exception as e:
        failed += 1
        tb = traceback.format_exc()
        errors.append((name, f"Exception: {e}"))
        print(f"  FAIL  {name}: Exception: {e}")


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── 1. Your First Program ────────────────────────────────────────────

section("1. Your First Program")

run_test("show hello world", 'show("Hello, World!")', expect_output="Hello, World!")

run_test("show multiple args", 'show("My name is" "TinyTalk" "and I am" 1 "years old")',
         expect_output="My name is TinyTalk and I am 1 years old")

run_test("show with variable interpolation", '''
let name = "Alice"
show("Hello" name)
''', expect_contains="Alice")

# ── 2. Variables ─────────────────────────────────────────────────────

section("2. Variables — Storing Stuff")

run_test("let and reassign", '''
let score = 0
score = 10
score += 5
score -= 3
score *= 2
show(score)
''', expect_output="24")

run_test("const prevents reassign", '''
const MAX = 3
MAX = 5
''', expect_fail=True)

run_test("string interpolation in let", '''
let name = "Alice"
let age = 25
show("Hi, I'm {name} and I'm {age}")
''', expect_output="Hi, I'm Alice and I'm 25")

# ── 3. Data Types ────────────────────────────────────────────────────

section("3. Data Types")

run_test("int type", 'show(42)', expect_output="42")
run_test("float type", 'show(3.14)', expect_output="3.14")
run_test("string type", 'show("hello")', expect_output="hello")
run_test("boolean true", 'show(true)', expect_output="true")
run_test("boolean false", 'show(false)', expect_output="false")
run_test("null type", 'show(null)', expect_output="null")

run_test("hex literal", 'show(0xFF)', expect_output="255")
run_test("octal literal", 'show(0o77)', expect_output="63")
run_test("binary literal", 'show(0b1010)', expect_output="10")

# ── 4. Math ──────────────────────────────────────────────────────────

section("4. Math — Crunching Numbers")

run_test("addition", 'show(2 + 3)', expect_output="5")
run_test("subtraction", 'show(10 - 4)', expect_output="6")
run_test("multiplication", 'show(3 * 7)', expect_output="21")
run_test("division", 'show(10 / 3)', expect_contains="3.33")
run_test("floor division", 'show(10 // 3)', expect_output="3")
run_test("modulo", 'show(10 % 3)', expect_output="1")
run_test("exponentiation", 'show(2 ** 10)', expect_output="1024")
run_test("order of operations", 'show(2 + 3 * 4)', expect_output="14")
run_test("parentheses", 'show((2 + 3) * 4)', expect_output="20")
run_test("string repeat", 'show("ha" * 3)', expect_output="hahaha")
run_test("string concat", 'show("hello" + " world")', expect_output="hello world")

# ── 5. Strings ───────────────────────────────────────────────────────

section("5. Strings — Working with Text")

run_test("string interpolation expr", '''
let name = "Alice"
let age = 25
show("My name is {name} and next year I'll be {age + 1}")
''', expect_output="My name is Alice and next year I'll be 26")

run_test("interpolation with math", 'show("5 squared is {5 * 5}")',
         expect_output="5 squared is 25")

# ── 6. Booleans & Comparisons ───────────────────────────────────────

section("6. Booleans & Comparisons")

run_test("equality", 'show(5 == 5)', expect_output="true")
run_test("inequality", 'show(5 != 3)', expect_output="true")
run_test("less than", 'show(3 < 5)', expect_output="true")
run_test("greater than", 'show(5 > 3)', expect_output="true")
run_test("less or equal", 'show(5 <= 5)', expect_output="true")
run_test("greater or equal", 'show(3 >= 5)', expect_output="false")
run_test("and operator", 'show(true and false)', expect_output="false")
run_test("or operator", 'show(true or false)', expect_output="true")
run_test("not operator", 'show(not true)', expect_output="false")

# ── 7. Lists ─────────────────────────────────────────────────────────

section("7. Lists — Collections of Things")

run_test("list creation and access", '''
let colors = ["red", "green", "blue"]
show(colors[0])
show(colors[1])
show(colors[-1])
''', expect_output="red\ngreen\nblue")

run_test("append and pop", '''
let items = [1, 2]
append(items, 3)
show(items)
pop(items)
show(items)
''', expect_contains=["[1, 2, 3]", "[1, 2]"])

run_test("list length", 'show(len([10, 20, 30]))', expect_output="3")
run_test("list .len property", 'show([10, 20, 30] .len)', expect_output="3")

# ── 8. Maps ──────────────────────────────────────────────────────────

section("8. Maps — Key-Value Pairs")

run_test("map creation and access", '''
let person = {"name": "Alice", "age": 25}
show(person["name"])
show(person.age)
''', expect_output="Alice\n25")

run_test("keys and values", '''
let m = {"a": 1, "b": 2, "c": 3}
show(keys(m))
show(values(m))
''', expect_contains=["a", "b", "c"])

# ── 9. If / Else ────────────────────────────────────────────────────

section("9. If / Else — Making Decisions")

run_test("basic if", '''
let temp = 35
if temp > 30 {
    show("It's hot!")
}
''', expect_output="It's hot!")

run_test("if/else", '''
let age = 16
if age >= 18 {
    show("You can vote!")
} else {
    show("Not old enough yet.")
}
''', expect_output="Not old enough yet.")

run_test("if/elif/else", '''
let score = 85
if score >= 90 {
    show("A")
} elif score >= 80 {
    show("B")
} elif score >= 70 {
    show("C")
} else {
    show("Keep trying!")
}
''', expect_output="B")

run_test("ternary expression", '''
let x = 10
let label = x > 5 ? "big" : "small"
show(label)
''', expect_output="big")

# ── 10. Loops ────────────────────────────────────────────────────────

section("10. Loops — Doing Things Repeatedly")

run_test("for loop with range", '''
let result = ""
for i in range(5) {
    result = result + str(i)
}
show(result)
''', expect_output="01234")

run_test("for loop over list", '''
let fruits = ["apple", "banana", "cherry"]
for fruit in fruits {
    show("I like {fruit}")
}
''', expect_output="I like apple\nI like banana\nI like cherry")

run_test("range with start and end", '''
let r = range(2, 6)
show(r)
''', expect_contains=["2", "3", "4", "5"])

run_test("range with step", '''
let r = range(0, 10, 2)
show(r)
''', expect_contains=["0", "2", "4", "6", "8"])

run_test("while loop", '''
let count = 0
let result = ""
while count < 5 {
    result = result + str(count)
    count += 1
}
show(result)
''', expect_output="01234")

run_test("break in loop", '''
for i in range(10) {
    if i == 5 { break }
    show(i)
}
''', expect_output="0\n1\n2\n3\n4")

run_test("continue in loop", '''
for i in range(5) {
    if i == 2 { continue }
    show(i)
}
''', expect_output="0\n1\n3\n4")

# ── 11. Functions ────────────────────────────────────────────────────

section("11. Functions — Reusable Blocks of Code")

run_test("basic function", '''
fn greet(name) {
    show("Hello, {name}!")
}
greet("Alice")
greet("Bob")
''', expect_output="Hello, Alice!\nHello, Bob!")

run_test("function with return", '''
fn square(x) {
    return x * x
}
show(square(5))
show(square(12))
''', expect_output="25\n144")

run_test("multiple parameters", '''
fn add(a, b) {
    return a + b
}
show(add(3, 4))
''', expect_output="7")

run_test("default parameter", '''
fn greet(name = "World") {
    show("Hello, {name}!")
}
greet()
greet("Alice")
''', expect_output="Hello, World!\nHello, Alice!")

run_test("default param mixed", '''
fn repeat_str(s, n = 3) {
    return s * n
}
show(repeat_str("ha"))
show(repeat_str("ho", 2))
''', expect_output="hahaha\nhoho")

run_test("recursion (factorial)", '''
fn factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
show(factorial(5))
''', expect_output="120")

# ── 12. Lambdas ──────────────────────────────────────────────────────

section("12. Lambdas — Quick Throwaway Functions")

run_test("simple lambda", '''
let double = (x) => x * 2
show(double(5))
''', expect_output="10")

run_test("lambda with two params", '''
let add = (a, b) => a + b
show(add(3, 4))
''', expect_output="7")

run_test("multi-line lambda", '''
let classify = (x) => {
    if x > 0 { return "positive" }
    if x < 0 { return "negative" }
    return "zero"
}
show(classify(5))
show(classify(-3))
show(classify(0))
''', expect_output="positive\nnegative\nzero")

run_test("lambda with step chains", '''
let nums = [1, 2, 3, 4, 5]
show(nums _filter((x) => x > 3))
show(nums _map((x) => x * 10))
''', expect_contains=["4, 5", "10, 20, 30, 40, 50"])

# ── 13. Step Chains ──────────────────────────────────────────────────

section("13. Step Chains — TinyTalk's Superpower")

run_test("sort and reverse", '''
let nums = [5, 3, 8, 1, 9]
show(nums _sort)
show(nums _reverse)
''', expect_contains=["1, 3, 5, 8, 9"])

run_test("filter", '''
let data = [1, 2, 3, 4, 5, 6, 7, 8]
show(data _filter((x) => x > 5))
show(data _filter((x) => x % 2 == 0))
''', expect_contains=["6, 7, 8", "2, 4, 6, 8"])

run_test("map (transform)", '''
let prices = [10, 20, 30]
show(prices _map((p) => p * 1.1))
''', expect_contains=["11", "22", "33"])

run_test("take and drop", '''
let items = [1, 2, 3, 4, 5, 6, 7, 8]
show(items _take(3))
show(items _drop(5))
''', expect_contains=["[1, 2, 3]", "[6, 7, 8]"])

run_test("first and last", '''
let items = [1, 2, 3, 4, 5, 6, 7, 8]
show(items _first)
show(items _last)
''', expect_output="1\n8")

run_test("sum avg min max count", '''
let scores = [85, 92, 78, 95, 88]
show(scores _sum)
show(scores _avg)
show(scores _min)
show(scores _max)
show(scores _count)
''', expect_output="438\n87.6\n78\n95\n5")

run_test("reduce sum", '''
show([1, 2, 3, 4, 5] _reduce((acc, x) => acc + x, 0))
''', expect_output="15")

run_test("reduce product", '''
show([1, 2, 3, 4, 5] _reduce((acc, x) => acc * x, 1))
''', expect_output="120")

run_test("reduce without init", '''
show([1, 2, 3, 4] _reduce((acc, x) => acc + x))
''', expect_output="10")

run_test("reduce string concat", '''
show(["a", "b", "c"] _reduce((acc, x) => acc + x, ""))
''', expect_output="abc")

run_test("unique", '''
let dupes = [1, 2, 2, 3, 3, 3, 4]
show(dupes _unique)
''', expect_contains=["1, 2, 3, 4"])

run_test("group", '''
let nums = [1, 2, 3, 4, 5, 6]
let grouped = nums _group((x) => x % 2 == 0 ? "even" : "odd")
show(grouped)
''', expect_contains=["even", "odd"])

run_test("flatten", '''
show([[1, 2], [3, 4], [5, 6]] _flatten)
''', expect_contains=["1, 2, 3, 4, 5, 6"])

run_test("chunk", '''
let seq = [1, 2, 3, 4, 5, 6]
show(seq _chunk(2))
''', expect_contains=["[1, 2]", "[3, 4]", "[5, 6]"])

run_test("zip", '''
let names = ["Alice", "Bob", "Charlie"]
let ages = [25, 30, 35]
show(names _zip(ages))
''', expect_contains=["Alice", "25", "Bob", "30"])

run_test("sortBy", '''
let people = [{"name": "Charlie", "age": 20}, {"name": "Alice", "age": 30}]
let sorted = people _sortBy((p) => p["age"])
show(sorted[0]["name"])
''', expect_output="Charlie")

run_test("join datasets", '''
let users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
let scores = [{"id": 1, "score": 95}, {"id": 2, "score": 87}]
let joined = users _join(scores, (r) => r["id"])
show(joined[0]["name"])
show(joined[0]["score"])
''', expect_output="Alice\n95")

run_test("mapValues", '''
let grouped = {"math": [90, 85, 92], "science": [88, 76, 95]}
let avgs = grouped _mapValues((scores) => scores _avg)
show(avgs)
''', expect_contains=["math", "science"])

run_test("each (side effect)", '''
let result = [1, 2, 3] _each((x) => show("item {x}"))
show(result)
''', expect_contains=["item 1", "item 2", "item 3"])

run_test("complex chain", '''
let data = [42, 17, 93, 5, 68, 31, 84, 12, 56, 29]
let result = data _filter((x) => x > 20) _sort _reverse _take(3) _map((x) => x * 10)
show(result)
''', expect_contains=["930", "840", "680"])

# ── 14. Natural Comparisons ──────────────────────────────────────────

section("14. Natural Comparisons")

run_test("is / isnt", '''
show(5 is 5)
show(5 isnt 3)
''', expect_output="true\ntrue")

run_test("has / hasnt", '''
let fruits = ["apple", "banana", "cherry"]
show(fruits has "banana")
show(fruits has "grape")
show(fruits hasnt "grape")
''', expect_output="true\nfalse\ntrue")

run_test("isin", '''
let fruits = ["apple", "banana", "cherry"]
show("banana" isin fruits)
''', expect_output="true")

run_test("islike wildcard", '''
show("hello" islike "hel*")
show("hello" islike "h?llo")
show("hello" islike "world*")
''', expect_output="true\ntrue\nfalse")

# ── 15. Property Conversions ─────────────────────────────────────────

section("15. Property Conversions — Dot Magic")

run_test("number to string", 'show(42 .str)', expect_output="42")
run_test("string to int", 'show("42" .int)', expect_output="42")
run_test("string to float", 'show("3.14" .float)', expect_output="3.14")
run_test("zero to bool", 'show(0 .bool)', expect_output="false")
run_test("one to bool", 'show(1 .bool)', expect_output="true")
run_test("empty string to bool", 'show("" .bool)', expect_output="false")
run_test("nonempty string to bool", 'show("hi" .bool)', expect_output="true")
run_test("type of int", 'show(42 .type)', expect_output="int")
run_test("type of string", 'show("hi" .type)', expect_output="string")
run_test("type of list", 'show([1,2] .type)', expect_output="list")
run_test("string .len", 'show("hello" .len)', expect_output="5")
run_test("list .len", 'show([1, 2, 3] .len)', expect_output="3")

# ── 16. String Methods ───────────────────────────────────────────────

section("16. String Methods — Text Tricks")

run_test("upcase", 'show("hello".upcase)', expect_output="HELLO")
run_test("downcase", 'show("HELLO".downcase)', expect_output="hello")
run_test("trim", 'show("  hello  ".trim)', expect_output="hello")
run_test("reversed", 'show("abc".reversed)', expect_output="cba")
run_test("chars", 'show("abc".chars)', expect_contains=["a", "b", "c"])
run_test("words", 'show("hello world".words)', expect_contains=["hello", "world"])

run_test("upcase function", 'show(upcase("hello"))', expect_output="HELLO")
run_test("downcase function", 'show(downcase("HELLO"))', expect_output="hello")
run_test("trim function", 'show(trim("  hello  "))', expect_output="hello")
run_test("replace function", 'show(replace("hello world", "world", "TinyTalk"))',
         expect_output="hello TinyTalk")
run_test("split function", 'show(split("a,b,c", ","))', expect_contains=["a", "b", "c"])
run_test("join function", 'show(join(["a", "b", "c"], "-"))', expect_output="a-b-c")
run_test("startswith", 'show(startswith("hello", "hel"))', expect_output="true")
run_test("endswith", 'show(endswith("hello", "llo"))', expect_output="true")

# ── 17. Match / Pattern Matching ─────────────────────────────────────

section("17. Match — Pattern Matching")

run_test("match basic", '''
let day = 3
match day {
    1 => show("Monday"),
    2 => show("Tuesday"),
    3 => show("Wednesday"),
    _ => show("Other"),
}
''', expect_output="Wednesday")

run_test("match as expression", '''
fn describe(x) {
    let result = match x {
        1 => "one",
        2 => "two",
        3 => "three",
        _ => "many",
    }
    return result
}
show(describe(2))
show(describe(99))
''', expect_output="two\nmany")

# ── 18. Try / Catch ──────────────────────────────────────────────────

section("18. Try / Catch — Handling Errors")

run_test("try/catch division by zero", '''
try {
    let result = 10 / 0
    show(result)
} catch(e) {
    show("caught error")
}
''', expect_contains="caught")

run_test("throw and catch", '''
fn divide(a, b) {
    if b == 0 {
        throw "Cannot divide by zero!"
    }
    return a / b
}
try {
    show(divide(10, 0))
} catch(e) {
    show("Error: " + e)
}
''', expect_contains="Cannot divide by zero")

# ── 19. Structs ──────────────────────────────────────────────────────

section("19. Structs — Custom Data Shapes")

run_test("struct creation", '''
struct Point {
    x: int,
    y: int,
}
let p = Point(3, 4)
show(p.x)
show(p.y)
''', expect_output="3\n4")

# ── 20. Blueprints ───────────────────────────────────────────────────

section("20. Blueprints — Objects with Behavior")

run_test("blueprint counter", '''
blueprint Counter
    field value = 0
    forge inc()
        self.value = self.value + 1
        reply self.value
    end
    forge reset()
        self.value = 0
        reply self.value
    end
end

let c = Counter(0)
show(c.inc())
show(c.inc())
show(c.inc())
show(c.reset())
''', expect_output="1\n2\n3\n0")

run_test("blueprint dog", '''
blueprint Dog
    field name = ""
    field energy = 100
    forge bark()
        self.energy = self.energy - 10
        reply "{self.name} says Woof! (energy: {self.energy})"
    end
    forge rest()
        self.energy = self.energy + 20
        reply "{self.name} rests. (energy: {self.energy})"
    end
end

let d = Dog("Rex", 100)
show(d.bark())
show(d.rest())
''', expect_contains=["Woof", "energy: 90", "energy: 110"])

# ── 21. Pipe Operator ────────────────────────────────────────────────

section("21. Pipe Operator")

run_test("pipe |>", '''
fn double(x) { return x * 2 }
fn add_one(x) { return x + 1 }
show(5 |> double |> add_one)
''', expect_output="11")

run_test("pipe %>%", '''
fn double(x) { return x * 2 }
fn add_one(x) { return x + 1 }
show(5 %>% double %>% add_one)
''', expect_output="11")

run_test("pipe mixed", '''
fn double(x) { return x * 2 }
fn add_one(x) { return x + 1 }
show(5 |> double %>% add_one)
''', expect_output="11")

# ── 22. Classic Style ────────────────────────────────────────────────

section("22. Classic Style — Smalltalk Flavor")

run_test("when constant", '''
when PI = 3.14159
show(PI)
''', expect_contains="3.14159")

run_test("law function", '''
when PI = 3.14159
law circle_area(r)
    reply PI * r * r
end
show(circle_area(5))
''', expect_contains="78.53")

run_test("forge function", '''
forge greet(name)
    reply "Hello, " + name
end
show(greet("World"))
''', expect_output="Hello, World")

# ── 23. Data I/O ─────────────────────────────────────────────────────

section("23. Data I/O — Reading & Writing Files")

# Create temp CSV for testing
_io_dir = os.path.dirname(os.path.abspath(__file__))
test_csv_path = os.path.join(_io_dir, "_test_data.csv")
with open(test_csv_path, "w") as f:
    f.write("name,age,score\nAlice,25,95.5\nBob,30,87.2\nCharlie,22,91.0\n")

test_json_path = os.path.join(_io_dir, "_test_data.json")
with open(test_json_path, "w") as f:
    f.write('{"database": {"host": "localhost", "port": 5432}}')

# Use a kernel with source_dir set so relative paths resolve
_saved_kernel = kernel
kernel = TinyTalkKernel(source_dir=_io_dir)

run_test("read_csv", f'''
let people = read_csv("{test_csv_path}")
show(people[0]["name"])
show(people[0]["age"])
''', expect_output="Alice\n25")

run_test("read_json", f'''
let config = read_json("{test_json_path}")
show(config["database"]["host"])
''', expect_output="localhost")

run_test("parse_json roundtrip", '''
let original = {"x": 1, "y": 2}
let json_str = to_json(original)
let parsed = parse_json(json_str)
show(parsed["x"])
show(parsed["y"])
''', expect_output="1\n2")

run_test("parse_json array", '''
let arr = parse_json("[1, 2, 3]")
show(arr _sum)
''', expect_output="6")

run_test("to_json", '''
let s = to_json([1, 2, 3])
show(s)
''', expect_contains="[1, 2, 3]")

_test_out_csv = os.path.join(_io_dir, "_test_out.csv")
_test_out_json = os.path.join(_io_dir, "_test_out.json")

# Write CSV test
run_test("write_csv", f'''
let data = [{{"name": "Test", "val": 42}}]
write_csv(data, "{_test_out_csv}")
show("written")
''', expect_contains="written")

# Write JSON test
run_test("write_json", f'''
let data = {{"users": 42, "active": true}}
write_json(data, "{_test_out_json}")
show("written")
''', expect_contains="written")

# Restore default kernel
kernel = _saved_kernel

# Cleanup IO test files
for f in [test_csv_path, test_json_path, _test_out_csv, _test_out_json]:
    try:
        os.remove(f)
    except OSError:
        pass

# ── 25. Dates & Time ─────────────────────────────────────────────────

section("25. Dates & Time")

run_test("date_now", '''
let now = date_now()
show(now)
''', expect_contains="202")

run_test("date_parse", '''
show(date_parse("2024-03-15"))
''', expect_contains="2024-03-15")

run_test("date_add days", '''
show(date_add("2024-03-15", 10, "days"))
''', expect_contains="2024-03-25")

run_test("date_diff", '''
show(date_diff("2024-03-20", "2024-03-15", "days"))
''', expect_contains="5")

run_test("date_floor month", '''
show(date_floor("2024-03-15", "month"))
''', expect_contains="2024-03-01")

run_test("date_format", '''
show(date_format("2024-03-15", "%B %d, %Y"))
''', expect_contains="March 15, 2024")

# ── 26. Data Analysis (dplyr-style) ──────────────────────────────────

section("26. Data Analysis — dplyr-Style Pipelines")

run_test("_select columns", '''
let people = [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "LA"}
]
show(people _select(["name", "age"]))
''', expect_contains=["Alice", "30", "Bob", "25"])

run_test("_mutate add columns", '''
let orders = [{"item": "Widget", "qty": 5, "price": 10}]
let enriched = orders _mutate((r) => {"total": r["qty"] * r["price"]})
show(enriched[0]["total"])
show(enriched[0]["item"])
''', expect_output="50\nWidget")

run_test("_summarize", '''
let data = [{"val": 10}, {"val": 20}, {"val": 30}]
let summary = data _summarize({
    "total": (rows) => rows _map((r) => r["val"]) _sum,
    "mean": (rows) => rows _map((r) => r["val"]) _avg,
    "n": (rows) => rows _count
})
show(summary)
''', expect_contains=["60", "20", "3"])

run_test("_rename columns", '''
let data = [{"first_name": "Alice", "last_name": "Smith"}]
let clean = data _rename({"first_name": "first", "last_name": "last"})
show(clean[0]["first"])
''', expect_output="Alice")

run_test("_arrange ascending", '''
let people = [{"name": "Charlie", "age": 20}, {"name": "Alice", "age": 30}]
let asc = people _arrange((r) => r["age"])
show(asc[0]["name"])
''', expect_output="Charlie")

run_test("_arrange descending", '''
let people = [{"name": "Charlie", "age": 20}, {"name": "Alice", "age": 30}]
let desc = people _arrange((r) => r["age"], "desc")
show(desc[0]["name"])
''', expect_output="Alice")

run_test("_distinct", '''
show([1, 2, 2, 3, 3] _distinct)
''', expect_contains=["1, 2, 3"])

run_test("_pull column", '''
let people = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
show(people _pull("name"))
show(people _pull("age") _avg)
''', expect_contains=["Alice", "Bob", "27.5"])

run_test("_slice", '''
let data = [10, 20, 30, 40, 50]
show(data _slice(1, 3))
show(data _slice(2))
''', expect_contains=["20, 30, 40", "30, 40, 50"])

run_test("_leftJoin", '''
let users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}, {"id": 3, "name": "Charlie"}]
let scores = [{"id": 1, "score": 95}, {"id": 2, "score": 87}]
let joined = users _leftJoin(scores, (r) => r["id"])
show(joined[0]["name"])
show(joined[2]["name"])
''', expect_output="Alice\nCharlie")

run_test("complete data analysis pipeline", '''
let employees = [
    {"name": "Alice",   "dept": "eng",   "salary": 120},
    {"name": "Bob",     "dept": "eng",   "salary": 100},
    {"name": "Charlie", "dept": "sales", "salary": 90},
    {"name": "Diana",   "dept": "sales", "salary": 110},
    {"name": "Eve",     "dept": "eng",   "salary": 130}
]
let top = employees
    _filter((r) => r["salary"] > 95)
    _mutate((r) => {"bonus": r["salary"] * 0.1})
    _arrange((r) => r["salary"], "desc")
    _select(["name", "salary", "bonus"])
show(top[0]["name"])
show(top _count)
''', expect_output="Eve\n4")

# ── 27. Reshaping Data — Pivot & Unpivot ─────────────────────────────

section("27. Reshaping Data — Pivot & Unpivot")

run_test("_pivot long to wide", '''
let sales = [{"region": "East", "product": "A", "revenue": 100}, {"region": "East", "product": "B", "revenue": 200}, {"region": "West", "product": "A", "revenue": 150}, {"region": "West", "product": "B", "revenue": 300}]
let wide = sales _pivot((r) => r["region"], (r) => r["product"], (r) => r["revenue"])
show(wide _count)
show(wide[0])
''', expect_contains=["2", "East", "100", "200"])

run_test("_unpivot wide to long", '''
let quarterly = [
    {"region": "East", "Q1": 100, "Q2": 200, "Q3": 150},
    {"region": "West", "Q1": 300, "Q2": 250, "Q3": 400}
]
let long = quarterly _unpivot(["region"])
show(long _count)
''', expect_output="6")

# ── 28. Rolling Aggregates — Window Functions ─────────────────────────

section("28. Rolling Aggregates — Window Functions")

run_test("_window moving average", '''
let prices = [10, 12, 11, 15, 14, 16, 18, 17, 20, 19]
let ma3 = prices _window(3, (w) => round(w _avg, 1))
show(ma3)
''', expect_contains=["10", "11", "12"])

run_test("_window rolling sum", '''
let data = [1, 2, 3, 4, 5]
show(data _window(2, (w) => w _sum))
''', expect_contains=["1", "3", "5", "7", "9"])

run_test("_window rolling max", '''
let temps = [3, 1, 4, 1, 5, 9, 2, 6]
show(temps _window(3, (w) => w _max))
''', expect_contains=["3", "4", "5", "9"])

run_test("_window chained", '''
let prices = [100, 102, 98, 105, 110, 108, 115, 120]
let above_threshold = prices
    _window(3, (w) => w _avg)
    _filter((x) => x > 105)
    _count
show(above_threshold)
''', expect_contains="3")

# ── 29. Python Transpiler ────────────────────────────────────────────

section("29. Python Transpiler")

code_for_transpile = '''let data = [1, 2, 3, 4, 5]
let result = data _filter((x) => x > 3) _sort _reverse _take(3)
show(result)'''

try:
    py_output = transpile(code_for_transpile)
    if "data" in py_output and "print" in py_output:
        passed += 1
        print(f"  PASS  transpile to Python")
    else:
        failed += 1
        errors.append(("transpile to Python", f"Unexpected output: {py_output[:200]}"))
        print(f"  FAIL  transpile to Python: unexpected output")
except Exception as e:
    failed += 1
    errors.append(("transpile to Python", str(e)))
    print(f"  FAIL  transpile to Python: {e}")

try:
    pandas_output = transpile_pandas(code_for_transpile)
    if "pandas" in pandas_output or "pd" in pandas_output:
        passed += 1
        print(f"  PASS  transpile to pandas")
    else:
        failed += 1
        errors.append(("transpile to pandas", f"Unexpected output: {pandas_output[:200]}"))
        print(f"  FAIL  transpile to pandas: unexpected output")
except Exception as e:
    failed += 1
    errors.append(("transpile to pandas", str(e)))
    print(f"  FAIL  transpile to pandas: {e}")

# ── 30. SQL Transpiler ───────────────────────────────────────────────

section("30. SQL Transpiler")

sql_code = 'employees _filter((r) => r["salary"] > 50000) _select("name", "dept", "salary") _arrange((r) => r["salary"], "desc") _take(10)'

try:
    sql_output = transpile_sql(sql_code)
    has_select = "SELECT" in sql_output
    has_where = "WHERE" in sql_output
    has_order = "ORDER BY" in sql_output
    has_limit = "LIMIT" in sql_output
    if has_select and has_where and has_order and has_limit:
        passed += 1
        print(f"  PASS  transpile to SQL")
    else:
        failed += 1
        msg = f"Missing clauses. SELECT={has_select} WHERE={has_where} ORDER={has_order} LIMIT={has_limit}"
        errors.append(("transpile to SQL", msg))
        print(f"  FAIL  transpile to SQL: {msg}")
except Exception as e:
    failed += 1
    errors.append(("transpile to SQL", str(e)))
    print(f"  FAIL  transpile to SQL: {e}")

# SQL group + summarize
sql_group_code = '''employees
    _group((r) => r["dept"])
    _summarize({
        "avg_salary": (rows) => rows _map((r) => r["salary"]) _avg,
        "headcount":  (rows) => rows _count
    })'''

try:
    sql_group_out = transpile_sql(sql_group_code)
    if "AVG" in sql_group_out and "COUNT" in sql_group_out:
        passed += 1
        print(f"  PASS  SQL group + summarize")
    else:
        failed += 1
        errors.append(("SQL group + summarize", f"Missing AVG or COUNT: {sql_group_out[:200]}"))
        print(f"  FAIL  SQL group + summarize")
except Exception as e:
    failed += 1
    errors.append(("SQL group + summarize", str(e)))
    print(f"  FAIL  SQL group + summarize: {e}")

# ── 32. Type Annotations ─────────────────────────────────────────────

section("32. Type Annotations — Optional Safety")

run_test("typed variables", '''
let name: str = "Alice"
let age: int = 25
let score: float = 98.5
let active: bool = true
show(name)
show(age)
''', expect_output="Alice\n25")

run_test("type mismatch error", '''
let x: int = "hello"
''', expect_fail=True)

run_test("typed function", '''
fn calculate_tax(income: float, rate: float = 0.08): float {
    return income * rate
}
show(calculate_tax(1000.0))
show(calculate_tax(1000.0, 0.1))
''', expect_output="80.0\n100.0")

run_test("optional type ?map", '''
fn find_user(id: int): ?map {
    if id == 0 { return null }
    return {"id": id, "name": "User " + str(id)}
}
show(find_user(1))
show(find_user(0))
''', expect_contains=["User 1", "null"])

# ── 33. Built-in Functions ───────────────────────────────────────────

section("33. Built-in Functions — Standard Toolkit")

# Math functions
run_test("abs", 'show(abs(-5))', expect_output="5")
run_test("round", 'show(round(3.456, 2))', expect_output="3.46")
run_test("floor", 'show(floor(3.7))', expect_output="3")
run_test("ceil", 'show(ceil(3.2))', expect_output="4")
run_test("sqrt", 'show(sqrt(16))', expect_output="4.0")
run_test("pow", 'show(pow(2, 10))', expect_contains="1024")
run_test("min", 'show(min(3, 1, 2))', expect_output="1")
run_test("max", 'show(max(3, 1, 2))', expect_output="3")
run_test("sum", 'show(sum([1,2,3]))', expect_output="6")

# Trig/log
run_test("sin", 'show(round(sin(0), 2))', expect_output="0.0")
run_test("cos", 'show(round(cos(0), 2))', expect_output="1.0")
run_test("log", 'show(round(log(E), 2))', expect_output="1.0")
run_test("exp", 'show(round(exp(1), 2))', expect_contains="2.72")

# Collections
run_test("range(n)", 'show(range(4))', expect_contains=["0", "1", "2", "3"])
run_test("range(a,b)", 'show(range(2,5))', expect_contains=["2", "3", "4"])
run_test("range(a,b,s)", 'show(range(0,10,3))', expect_contains=["0", "3", "6", "9"])
run_test("sort function", 'show(sort([3,1,2]))', expect_contains=["1, 2, 3"])
run_test("reverse function", 'show(reverse([1,2,3]))', expect_contains=["3, 2, 1"])
run_test("contains function", 'show(contains([1,2], 2))', expect_output="true")
run_test("slice function", 'show(slice([1,2,3,4], 1, 3))', expect_contains=["2", "3"])
run_test("keys function", 'show(keys({"a":1}))', expect_contains="a")
run_test("values function", 'show(values({"a":1}))', expect_contains="1")
run_test("zip function", 'show(zip([1,2],[3,4]))', expect_contains=["1", "3"])
run_test("enumerate function", 'show(enumerate(["a","b"]))', expect_contains=["0", "a", "1", "b"])

# Type conversion functions
run_test("str()", 'show(str(42))', expect_output="42")
run_test("int()", 'show(int("42"))', expect_output="42")
run_test("float()", 'show(float("3.14"))', expect_output="3.14")
run_test("bool(0)", 'show(bool(0))', expect_output="false")
run_test("type()", 'show(type(42))', expect_output="int")

# Assertions
run_test("assert true", 'assert(true, "should pass")', expect_success=True)
run_test("assert_equal", 'assert_equal(1, 1, "should pass")', expect_success=True)
run_test("assert fails", 'assert(false, "should fail")', expect_fail=True)

# Built-in constants
run_test("PI constant", 'show(round(PI, 5))', expect_contains="3.14159")
run_test("E constant", 'show(round(E, 5))', expect_contains="2.71828")
run_test("TAU constant", 'show(round(TAU, 4))', expect_contains="6.2832")
run_test("INF constant", 'show(INF > 999999)', expect_output="true")

# ── Fibonacci stress (from examples) ─────────────────────────────────

section("Extra: Fibonacci Stress Test")

run_test("fibonacci 15 values", '''
fn fib(n) {
    if n <= 1 { return n }
    return fib(n - 1) + fib(n - 2)
}
show(fib(0))
show(fib(1))
show(fib(10))
show(fib(15))
''', expect_output="0\n1\n55\n610")

# ── Step chains from examples ─────────────────────────────────────────

section("Extra: Full Step Chain Example")

run_test("step chains example file", '''
let data = [42, 17, 93, 5, 68, 31, 84, 12, 56, 29]
show("Top 5:" data _sort _reverse _take(5))
show("Count > 30:" data _filter((x) => x > 30) _count)
show("Doubled sum:" data _map((x) => x * 2) _sum)
let dupes = [1, 2, 2, 3, 3, 3, 4]
show("Unique:" dupes _unique)
let result = data _filter((x) => x > 20) _sort _map((x) => x * 10) _take(3)
show("Filtered:" result)
let nums = [1, 2, 3, 4, 5, 6, 7, 8]
let grouped = nums _group((x) => x % 2 == 0 ? "even" : "odd")
show("Grouped:" grouped)
let nested = [[1, 2], [3, 4], [5, 6]]
show("Flattened:" nested _flatten)
let seq = [1, 2, 3, 4, 5, 6]
show("Chunked:" seq _chunk(2))
show("Min:" data _min)
show("Max:" data _max)
show("Sum:" data _sum)
show("Avg:" data _avg)
''', expect_contains=["Top 5", "Count > 30", "Doubled sum", "Unique",
                       "Filtered", "Grouped", "Flattened", "Chunked",
                       "Min", "Max", "Sum", "Avg"])

# ── Mixed Modern + Classic Style ─────────────────────────────────────

section("Extra: Mixed Modern + Classic Styles")

run_test("mixed styles in one program", '''
when PI = 3.14159

law circle_area(r)
    reply PI * r * r
end

let radius = 5
let area = circle_area(radius)
show("Circle area: {round(area, 2)}")

fn square(x) {
    return x * x
}
show("Square of 7: {square(7)}")

blueprint Counter
    field value = 0
    forge inc()
        self.value = self.value + 1
        reply self.value
    end
end

let c = Counter(0)
show("Counter: {c.inc()} {c.inc()} {c.inc()}")
''', expect_contains=["Circle area: 78.54", "Square of 7: 49", "Counter: 1 2 3"])

# ── Edge Cases & Stress ──────────────────────────────────────────────

section("Extra: Edge Cases & Stress")

run_test("empty list operations", '''
let empty = []
show(empty _count)
show(empty _sum)
show(len(empty))
''', expect_output="0\n0\n0")

run_test("deeply nested data", '''
let data = {"a": {"b": {"c": 42}}}
show(data["a"]["b"]["c"])
''', expect_output="42")

run_test("string interpolation complex", '''
let x = 10
let y = 20
show("{x} + {y} = {x + y}, {x} * {y} = {x * y}")
''', expect_output="10 + 20 = 30, 10 * 20 = 200")

run_test("chained comparison ops", '''
show(1 < 2 and 2 < 3 and 3 < 4)
show(5 > 3 or 2 > 10)
show(not (1 > 2))
''', expect_output="true\ntrue\ntrue")

run_test("list of maps pipeline", '''
let people = [
    {"name": "Zara", "score": 88},
    {"name": "Alex", "score": 95},
    {"name": "Mike", "score": 72},
    {"name": "Lucy", "score": 91},
    {"name": "John", "score": 85}
]
let top3 = people
    _sortBy((p) => p["score"])
    _reverse
    _take(3)
    _map((p) => p["name"])
show(top3)
''', expect_contains=["Alex", "Lucy", "Zara"])

run_test("many operations chained", '''
let result = range(1, 21)
    _filter((x) => x % 2 == 0)
    _map((x) => x * x)
    _filter((x) => x > 50)
    _sort
    _reverse
    _take(3)
show(result)
''', expect_contains=["400", "324", "256"])

run_test("nested function calls", '''
fn double(x) { return x * 2 }
fn add(a, b) { return a + b }
show(add(double(3), double(4)))
''', expect_output="14")

run_test("large list operations", '''
let big = range(1000)
show(big _count)
show(big _sum)
show(big _filter((x) => x > 990) _count)
''', expect_output="1000\n499500\n9")

# ── 37. Quick Reference Cheat Sheet (spot checks) ────────────────────

section("Extra: Quick Reference Spot Checks")

run_test("multiline list processing", '''
let data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
let evens = data _filter((x) => x % 2 == 0)
let doubled = evens _map((x) => x * 2)
let total = doubled _sum
show(total)
''', expect_output="60")

run_test("map iteration", '''
let m = {"x": 1, "y": 2, "z": 3}
let k = keys(m)
show(k _count)
''', expect_output="3")

run_test("string operations pipeline", '''
let words = split("hello world foo bar", " ")
show(words _count)
show(words _filter((w) => len(w) > 3) _count)
show(join(words, "-"))
''', expect_output="4\n2\nhello-world-foo-bar")


# ══════════════════════════════════════════════════════════════════════
# Final Report
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"  STRESS TEST COMPLETE")
print(f"{'='*60}")
print(f"  Total:   {passed + failed}")
print(f"  Passed:  {passed}")
print(f"  Failed:  {failed}")
print(f"{'='*60}")

if errors:
    print(f"\n  Failed tests:")
    for name, reason in errors:
        print(f"    - {name}: {reason}")

print()
sys.exit(0 if failed == 0 else 1)
