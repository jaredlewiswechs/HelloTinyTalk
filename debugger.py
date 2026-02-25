"""
TinyTalk Chain Debugger
Step-through debugging for step chains with intermediate result inspection.

The killer feature: hover over each step in a pipeline like
    data _filter(...) _sort _reverse _take(3)
and see the intermediate result at every underscore.

No other language does this. Python debuggers show you the final result
of a chained expression. TinyTalk shows you every stage.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .tt_types import Value, ValueType
from .stdlib import format_value


@dataclass
class StepSnapshot:
    """A snapshot of data at one point in a step chain."""
    step_name: str
    step_index: int
    args_repr: str
    result: Value
    result_preview: str
    item_count: Optional[int] = None
    elapsed_us: float = 0.0

    def to_dict(self) -> dict:
        return {
            "step": self.step_name,
            "index": self.step_index,
            "args": self.args_repr,
            "preview": self.result_preview,
            "count": self.item_count,
            "elapsed_us": round(self.elapsed_us, 1),
        }


@dataclass
class ChainDebugResult:
    """Full debug trace of a step chain execution."""
    source_repr: str
    source_count: Optional[int]
    steps: List[StepSnapshot] = field(default_factory=list)
    final_result: Optional[Value] = None

    def to_dict(self) -> dict:
        return {
            "source": self.source_repr,
            "source_count": self.source_count,
            "steps": [s.to_dict() for s in self.steps],
        }


def preview_value(val: Value, max_items: int = 5, max_chars: int = 200) -> str:
    """Create a compact preview of a value for debug display."""
    if val.type == ValueType.LIST:
        count = len(val.data)
        if count == 0:
            return "[] (empty)"
        items = val.data[:max_items]
        preview_parts = [format_value(v) for v in items]
        preview = "[" + ", ".join(preview_parts) + "]"
        if count > max_items:
            preview = preview[:-1] + f", ... +{count - max_items} more]"
        if len(preview) > max_chars:
            preview = preview[:max_chars - 3] + "..."
        return f"{preview} ({count} items)"
    if val.type == ValueType.MAP:
        count = len(val.data)
        preview = format_value(val)
        if len(preview) > max_chars:
            preview = preview[:max_chars - 3] + "..."
        return f"{preview} ({count} keys)"
    preview = format_value(val)
    if len(preview) > max_chars:
        preview = preview[:max_chars - 3] + "..."
    return preview


def count_items(val: Value) -> Optional[int]:
    """Count items in a collection value, or None for scalars."""
    if val.type == ValueType.LIST:
        return len(val.data)
    if val.type == ValueType.MAP:
        return len(val.data)
    if val.type == ValueType.STRING:
        return len(val.data)
    return None


class ChainDebugger:
    """Instruments step chain execution to capture intermediate results.

    Usage:
        debugger = ChainDebugger()
        # The runtime calls debugger.on_step() after each step
        trace = debugger.get_trace()  # Returns ChainDebugResult
    """

    def __init__(self):
        self.traces: List[ChainDebugResult] = []
        self._current: Optional[ChainDebugResult] = None

    def begin_chain(self, source: Value, source_repr: str = ""):
        """Called when a step chain begins execution."""
        self._current = ChainDebugResult(
            source_repr=source_repr or preview_value(source),
            source_count=count_items(source),
        )

    def on_step(self, step_name: str, step_index: int, args: list,
                result: Value, elapsed_us: float = 0.0):
        """Called after each step in the chain executes."""
        if self._current is None:
            return

        # Format args for display
        args_repr = ""
        if args:
            args_parts = []
            for a in args:
                if a.type == ValueType.FUNCTION:
                    args_parts.append("<fn>")
                else:
                    s = format_value(a)
                    if len(s) > 50:
                        s = s[:47] + "..."
                    args_parts.append(s)
            args_repr = ", ".join(args_parts)

        snapshot = StepSnapshot(
            step_name=step_name,
            step_index=step_index,
            args_repr=args_repr,
            result=result,
            result_preview=preview_value(result),
            item_count=count_items(result),
            elapsed_us=elapsed_us,
        )
        self._current.steps.append(snapshot)

    def end_chain(self, final_result: Value):
        """Called when the step chain completes."""
        if self._current:
            self._current.final_result = final_result
            self.traces.append(self._current)
            self._current = None

    def get_traces(self) -> List[dict]:
        """Return all captured chain traces as serializable dicts."""
        return [t.to_dict() for t in self.traces]

    def clear(self):
        """Clear all captured traces."""
        self.traces.clear()
        self._current = None
