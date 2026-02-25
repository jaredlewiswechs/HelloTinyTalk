"""
TinyTalk Python Interop
Bridge between TinyTalk and Python libraries.

Allows TinyTalk code to import and call Python modules:
    from python use requests
    let resp = requests.get("https://api.example.com/data")

The interpreter is already written in Python — the bridge wraps
Python modules and exposes them as TinyTalk maps of callable functions.
"""

from typing import Any, Dict, List, Optional
import importlib
import inspect

from .tt_types import Value, ValueType


def python_to_value(obj: Any) -> Value:
    """Convert an arbitrary Python object to a TinyTalk Value."""
    if obj is None:
        return Value.null_val()
    if isinstance(obj, bool):
        return Value.bool_val(obj)
    if isinstance(obj, int):
        return Value.int_val(obj)
    if isinstance(obj, float):
        return Value.float_val(obj)
    if isinstance(obj, str):
        return Value.string_val(obj)
    if isinstance(obj, bytes):
        return Value.string_val(obj.decode("utf-8", errors="replace"))
    if isinstance(obj, (list, tuple)):
        return Value.list_val([python_to_value(x) for x in obj])
    if isinstance(obj, dict):
        return Value.map_val({str(k): python_to_value(v) for k, v in obj.items()})
    if isinstance(obj, set):
        return Value.list_val([python_to_value(x) for x in obj])
    # For complex objects, wrap their public attributes as a map
    if hasattr(obj, "__dict__"):
        return _wrap_object(obj)
    return Value.string_val(str(obj))


def value_to_python(val: Value) -> Any:
    """Convert a TinyTalk Value to a native Python object."""
    return val.to_python()


def _wrap_object(obj: Any) -> Value:
    """Wrap a Python object as a TinyTalk map with callable methods."""
    result = {}
    # Expose public attributes
    for name in dir(obj):
        if name.startswith("_"):
            continue
        try:
            attr = getattr(obj, name)
        except Exception:
            continue
        if callable(attr):
            result[name] = _wrap_callable(attr, name)
        else:
            result[name] = python_to_value(attr)
    # Special: expose text/content/status_code for response-like objects
    for special in ("text", "content", "status_code", "json", "headers", "url"):
        if hasattr(obj, special) and special not in result:
            attr = getattr(obj, special)
            if callable(attr):
                result[special] = _wrap_callable(attr, special)
            else:
                result[special] = python_to_value(attr)
    return Value.map_val(result)


def _wrap_callable(fn: Any, name: str) -> Value:
    """Wrap a Python callable as a TinyTalk function value."""
    from .runtime import TinyFunction

    def bridge(args: List[Value]) -> Value:
        py_args = [value_to_python(a) for a in args]
        # Support keyword arguments passed as a final map
        kwargs = {}
        if py_args and isinstance(py_args[-1], dict):
            # Check if any key matches a parameter name
            try:
                sig = inspect.signature(fn)
                param_names = set(sig.parameters.keys())
                last = py_args[-1]
                if any(k in param_names for k in last):
                    kwargs = py_args.pop()
            except (ValueError, TypeError):
                pass
        try:
            result = fn(*py_args, **kwargs)
            return python_to_value(result)
        except Exception as e:
            raise ValueError(f"Python error in {name}(): {e}")

    return Value.function_val(TinyFunction(name, [], None, None, True, bridge))


def import_python_module(module_name: str, items: Optional[List[str]] = None) -> Dict[str, Value]:
    """Import a Python module and return its public API as TinyTalk values.

    Args:
        module_name: Python module name (e.g. "requests", "math", "os.path")
        items: Optional list of specific names to import

    Returns:
        Dict mapping names to TinyTalk Values (functions become callable)
    """
    try:
        mod = importlib.import_module(module_name)
    except ImportError as e:
        raise ValueError(
            f"Python module '{module_name}' not found. "
            f"Install it with: pip install {module_name}\n"
            f"Error: {e}"
        )

    result = {}

    if items:
        # Selective import: from python use requests { get, post }
        for name in items:
            if not hasattr(mod, name):
                raise ValueError(f"Python module '{module_name}' has no attribute '{name}'")
            attr = getattr(mod, name)
            if callable(attr):
                result[name] = _wrap_callable(attr, f"{module_name}.{name}")
            else:
                result[name] = python_to_value(attr)
    else:
        # Full module import: from python use requests
        for name in dir(mod):
            if name.startswith("_"):
                continue
            try:
                attr = getattr(mod, name)
            except Exception:
                continue
            if callable(attr):
                result[name] = _wrap_callable(attr, f"{module_name}.{name}")
            elif not inspect.ismodule(attr):
                result[name] = python_to_value(attr)

    return result


# Restricted modules that should not be importable from the sandbox
BLOCKED_MODULES = frozenset({
    "subprocess", "shutil", "ctypes", "multiprocessing",
    "signal", "resource", "pty", "fcntl", "termios",
})


def is_module_allowed(module_name: str, sandbox: bool = True) -> bool:
    """Check if a module is allowed to be imported."""
    if not sandbox:
        return True
    base = module_name.split(".")[0]
    return base not in BLOCKED_MODULES
