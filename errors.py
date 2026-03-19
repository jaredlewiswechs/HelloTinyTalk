"""
TinyTalk Error Messages That Teach

Provides helpful, educational error messages with:
  - "Did you mean?" suggestions for typos (Levenshtein distance)
  - Contextual hints for type mismatches
  - Step chain usage guidance
"""

from typing import List, Optional, Dict


# ---------------------------------------------------------------------------
# Edit distance (Levenshtein)
# ---------------------------------------------------------------------------

def _edit_distance(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        return _edit_distance(b, a)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[-1]


def find_closest(name: str, candidates: List[str], max_distance: int = 2) -> Optional[str]:
    """Find the closest match to `name` from a list of candidates."""
    if not candidates:
        return None
    best = None
    best_dist = max_distance + 1
    for c in candidates:
        d = _edit_distance(name.lower(), c.lower())
        if d < best_dist:
            best_dist = d
            best = c
    return best if best_dist <= max_distance else None


# ---------------------------------------------------------------------------
# Known step chain names and their valid contexts
# ---------------------------------------------------------------------------

ALL_STEP_NAMES = [
    "filter", "sort", "map", "take", "drop", "first", "last",
    "reverse", "unique", "count", "sum", "avg", "min", "max",
    "group", "flatten", "zip", "chunk", "reduce", "sortBy",
    "join", "mapValues", "each",
    "select", "mutate", "summarize", "rename", "arrange",
    "distinct", "slice", "pull", "groupBy", "group_by",
    "leftJoin", "left_join", "pivot", "unpivot", "window",
]

# Steps that require a list
STEPS_REQUIRING_LIST = {
    "filter", "sort", "map", "take", "drop", "first", "last",
    "reverse", "unique", "count", "sum", "avg", "min", "max",
    "flatten", "zip", "chunk", "reduce", "sortBy", "each",
    "select", "mutate", "rename", "arrange", "distinct",
    "slice", "pull", "leftJoin", "left_join",
    "pivot", "unpivot", "window",
}

# Steps that work on maps
STEPS_REQUIRING_MAP = {"mapValues"}

# Steps that can work on grouped maps (map of lists)
STEPS_ON_GROUPED = {"summarize"}


# ---------------------------------------------------------------------------
# Error message builders
# ---------------------------------------------------------------------------

def undefined_variable_hint(name: str, available: List[str]) -> str:
    """Build an error message for an undefined variable with suggestions."""
    msg = f"Undefined variable '{name}'"
    suggestion = find_closest(name, available)
    if suggestion:
        msg += f". Did you mean '{suggestion}'?"
    return msg


def unknown_step_hint(step_name: str) -> str:
    """Build an error message for an unknown step chain with suggestions."""
    msg = f"Unknown step '{step_name}'"
    suggestion = find_closest(step_name, ALL_STEP_NAMES)
    if suggestion:
        msg += f". Did you mean '{suggestion}'?"
    return msg


def step_type_mismatch_hint(step_name: str, actual_type: str) -> str:
    """Build an error message when a step is used on the wrong type."""
    if step_name in STEPS_REQUIRING_MAP:
        msg = f"'{step_name}' works on maps. You have a {actual_type}"
        if actual_type == "list":
            msg += f" — try converting to a map first with .group, or use .map instead."
        return msg

    if step_name in STEPS_REQUIRING_LIST:
        msg = f"'{step_name}' works on lists. You have a {actual_type}"
        if actual_type == "map":
            msg += f" — try keys(data) {step_name} or values(data) {step_name}."
        elif actual_type == "string":
            msg += f" — try data.chars {step_name} or data.words {step_name}."
        return msg

    return f"Step '{step_name}' requires a list, got {actual_type}"


def step_args_hint(step_name: str) -> str:
    """Provide usage hints for a step chain that received wrong arguments."""
    hints: Dict[str, str] = {
        "filter": ".filter requires a function: data.filter((x) => condition)",
        "map": ".map requires a function: data.map((x) => transform(x))",
        "sort": ".sort optionally takes a key function: data.sort or data.sort((x) => x.field)",
        "reduce": ".reduce requires a function and optional initial value: data.reduce((acc, x) => acc + x, 0)",
        "group": ".group requires a key function: data.group((x) => x.category)",
        "groupBy": ".groupBy requires a key function: data.groupBy((x) => x.category)",
        "join": ".join requires (right_list, key_fn): left.join(right, (r) => r.id)",
        "leftJoin": ".leftJoin requires (right_list, key_fn): left.leftJoin(right, (r) => r.id)",
        "left_join": ".left_join requires (right_list, key_fn): left.left_join(right, (r) => r.id)",
        "select": '.select requires column names: data.select(["name", "age"]) or data.select("name", "age")',
        "mutate": ".mutate requires a function returning a map: data.mutate((r) => {\"new_col\": value})",
        "summarize": ".summarize requires a map of aggregation functions: data.summarize({\"total\": (rows) => rows.sum})",
        "rename": ".rename requires a map of {old: new}: data.rename({\"old_name\": \"new_name\"})",
        "arrange": ".arrange requires a key function: data.arrange((r) => r.field)",
        "sortBy": ".sortBy requires a key function: data.sortBy((x) => x.field)",
        "each": ".each requires a function: data.each((x) => show(x))",
        "mapValues": ".mapValues requires a function: map_data.mapValues((v) => transform(v))",
        "zip": ".zip requires a list: list1.zip(list2)",
        "chunk": ".chunk requires a size: data.chunk(3)",
        "pivot": ".pivot requires (index_fn, column_fn, value_fn)",
        "unpivot": ".unpivot requires a list of id column names",
        "window": ".window requires (window_size, function)",
        "pull": '.pull requires a column name: data.pull("column_name")',
        "distinct": ".distinct optionally takes a key function or column list",
    }
    return hints.get(step_name, f"Check the usage of '{step_name}'")


def type_error_hint(operation: str, left_type: str, right_type: str) -> str:
    """Build a hint for type mismatches in operations."""
    msg = f"Cannot {operation} {left_type} and {right_type}"

    if operation in ("add", "+"):
        if left_type == "string" or right_type == "string":
            non_str = right_type if left_type == "string" else left_type
            msg += f". Convert to string first: value.str"
    elif operation in ("subtract", "-", "multiply", "*", "divide", "/"):
        if "string" in (left_type, right_type):
            msg += ". Arithmetic operations require numbers. Use .int or .float to convert."

    return msg


def function_call_hint(name: str, expected_args: int, actual_args: int) -> str:
    """Build a hint for wrong number of arguments."""
    if actual_args < expected_args:
        return f"'{name}' expects {expected_args} argument(s), but got {actual_args}. Missing {expected_args - actual_args} argument(s)."
    return f"'{name}' expects {expected_args} argument(s), but got {actual_args}. Too many arguments."
