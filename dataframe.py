"""
TinyTalk DataFrame — First-Class Columnar Data Type

A native DataFrame type backed by columnar storage that keeps the same
TinyTalk syntax while making tabular data competitive for real work.

Internally wraps a dict-of-lists (columnar) representation. When pandas
is available, large DataFrames automatically delegate to pandas for
performance. The TinyTalk API stays the same regardless.

Usage in TinyTalk:
    let df = DataFrame(data)         // from list of maps
    let df = read_csv("file.csv")    // auto-detects as DataFrame for large files
    df _filter((r) => r["age"] > 30) // same step chain syntax
    df _select("name", "age")        // column selection
    df.columns                       // list of column names
    df.shape                         // [rows, cols]
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from .tt_types import Value, ValueType


class TinyDataFrame:
    """Columnar representation of tabular data.

    Stores data as {column_name: [values...]}, which is more efficient
    than the default list-of-maps representation for column operations.
    """

    def __init__(self, columns: Optional[Dict[str, list]] = None, column_order: Optional[List[str]] = None):
        self.columns: Dict[str, list] = columns or {}
        self.column_order: List[str] = column_order or list(self.columns.keys())
        self._nrows = max((len(v) for v in self.columns.values()), default=0) if self.columns else 0

    @classmethod
    def from_rows(cls, rows: List[Dict[str, Any]]) -> TinyDataFrame:
        """Create a DataFrame from a list of row dicts (maps)."""
        if not rows:
            return cls()
        # Collect all column names preserving order
        col_order = []
        seen = set()
        for row in rows:
            for k in row:
                if k not in seen:
                    col_order.append(k)
                    seen.add(k)
        columns = {col: [] for col in col_order}
        for row in rows:
            for col in col_order:
                columns[col].append(row.get(col))
        return cls(columns, col_order)

    @classmethod
    def from_value_rows(cls, rows: List[Value]) -> TinyDataFrame:
        """Create a DataFrame from a list of TinyTalk map Values."""
        dicts = []
        for row in rows:
            if row.type == ValueType.MAP:
                dicts.append({k: v for k, v in row.data.items()})
        return cls.from_rows(dicts)

    @property
    def nrows(self) -> int:
        return self._nrows

    @property
    def ncols(self) -> int:
        return len(self.columns)

    @property
    def shape(self) -> tuple:
        return (self.nrows, self.ncols)

    def get_row(self, i: int) -> Dict[str, Any]:
        """Get a single row as a dict."""
        return {col: self.columns[col][i] for col in self.column_order}

    def get_column(self, name: str) -> list:
        """Get a single column as a list."""
        return self.columns.get(name, [])

    def to_rows(self) -> List[Dict[str, Any]]:
        """Convert back to list of dicts."""
        rows = []
        for i in range(self.nrows):
            rows.append(self.get_row(i))
        return rows

    def to_value_rows(self) -> List[Value]:
        """Convert to a list of TinyTalk map Values."""
        rows = []
        for i in range(self.nrows):
            row = {}
            for col in self.column_order:
                row[col] = self.columns[col][i]
            rows.append(Value.map_val(row))
        return rows

    def to_value(self) -> Value:
        """Convert to a TinyTalk list-of-maps Value for compatibility."""
        return Value.list_val(self.to_value_rows())

    def select(self, cols: List[str]) -> TinyDataFrame:
        """Select specific columns."""
        new_cols = {c: self.columns[c] for c in cols if c in self.columns}
        return TinyDataFrame(new_cols, [c for c in cols if c in self.columns])

    def filter_rows(self, mask: List[bool]) -> TinyDataFrame:
        """Filter rows by a boolean mask."""
        new_cols = {}
        for col in self.column_order:
            new_cols[col] = [v for v, m in zip(self.columns[col], mask) if m]
        return TinyDataFrame(new_cols, list(self.column_order))

    def sort_by(self, col: str, desc: bool = False) -> TinyDataFrame:
        """Sort by a column."""
        if col not in self.columns:
            return self
        indices = sorted(range(self.nrows),
                         key=lambda i: _sort_key(self.columns[col][i]),
                         reverse=desc)
        new_cols = {}
        for c in self.column_order:
            new_cols[c] = [self.columns[c][i] for i in indices]
        return TinyDataFrame(new_cols, list(self.column_order))

    def head(self, n: int) -> TinyDataFrame:
        """Take first n rows."""
        new_cols = {c: self.columns[c][:n] for c in self.column_order}
        return TinyDataFrame(new_cols, list(self.column_order))

    def tail(self, n: int) -> TinyDataFrame:
        """Take last n rows."""
        new_cols = {c: self.columns[c][-n:] for c in self.column_order}
        return TinyDataFrame(new_cols, list(self.column_order))

    def rename(self, mapping: Dict[str, str]) -> TinyDataFrame:
        """Rename columns."""
        new_cols = {}
        new_order = []
        for c in self.column_order:
            new_name = mapping.get(c, c)
            new_cols[new_name] = self.columns[c]
            new_order.append(new_name)
        return TinyDataFrame(new_cols, new_order)

    def add_column(self, name: str, values: list) -> TinyDataFrame:
        """Add a new column (returns new DataFrame)."""
        new_cols = dict(self.columns)
        new_cols[name] = values
        new_order = list(self.column_order)
        if name not in new_order:
            new_order.append(name)
        return TinyDataFrame(new_cols, new_order)

    def to_list(self) -> Value:
        """Convert back to a TinyTalk list-of-maps. The escape hatch."""
        return Value.list_val(self.to_value_rows())


def _sort_key(val):
    """Extract a sortable key from a TinyTalk Value."""
    if isinstance(val, Value):
        if val.type in (ValueType.INT, ValueType.FLOAT):
            return (0, val.data)
        if val.type == ValueType.STRING:
            return (1, val.data)
        if val.type == ValueType.NULL:
            return (2, "")
        return (3, str(val.data))
    return (3, str(val))


# ---------------------------------------------------------------------------
# Performance optimization: auto-detect large datasets
# ---------------------------------------------------------------------------

# Threshold above which we use optimized paths
LARGE_DATASET_THRESHOLD = 1000


def should_use_fast_path(data: Value) -> bool:
    """Check if a dataset is large enough to benefit from optimized execution."""
    if data.type != ValueType.LIST:
        return False
    return len(data.data) >= LARGE_DATASET_THRESHOLD


def try_pandas_fast_path(data: Value, step: str, args: list) -> Optional[Value]:
    """Attempt to execute a step chain using pandas for large datasets.

    Returns None if pandas is not available or the operation is not supported.
    This is the performance floor: tree-walking is fine for small data,
    but when someone loads a 100K-row CSV, the hot path drops into pandas.
    """
    if not should_use_fast_path(data):
        return None

    try:
        import pandas as pd
    except ImportError:
        return None

    # Convert list-of-maps to DataFrame
    rows = []
    for item in data.data:
        if item.type == ValueType.MAP:
            rows.append({k: v.to_python() for k, v in item.data.items()})
        else:
            return None  # Not tabular data

    if not rows:
        return None

    df = pd.DataFrame(rows)

    try:
        if step == "_sort":
            if not args:
                # Sort by first column
                df = df.sort_values(by=df.columns[0])
            return _df_to_value(df)

        if step == "_reverse":
            df = df.iloc[::-1].reset_index(drop=True)
            return _df_to_value(df)

        if step == "_take":
            n = int(args[0].data) if args else 1
            df = df.head(n)
            return _df_to_value(df)

        if step == "_drop":
            n = int(args[0].data) if args else 1
            df = df.iloc[n:]
            return _df_to_value(df)

        if step == "_count":
            return Value.int_val(len(df))

        if step == "_sum":
            total = df.select_dtypes(include='number').sum().sum()
            return Value.float_val(float(total))

        if step == "_avg":
            avg = df.select_dtypes(include='number').mean().mean()
            return Value.float_val(float(avg))

        if step == "_unique" or step == "_distinct":
            df = df.drop_duplicates()
            return _df_to_value(df)

        if step == "_select" and args:
            if args[0].type == ValueType.LIST:
                cols = [v.data for v in args[0].data]
            elif args[0].type == ValueType.STRING:
                cols = [a.data for a in args if a.type == ValueType.STRING]
            else:
                return None
            valid_cols = [c for c in cols if c in df.columns]
            if valid_cols:
                df = df[valid_cols]
                return _df_to_value(df)

    except Exception:
        return None  # Fall back to tree-walking

    return None  # Unsupported step — fall back


def _df_to_value(df) -> Value:
    """Convert a pandas DataFrame back to a TinyTalk list-of-maps Value."""
    from .stdlib import _python_to_value
    rows = df.to_dict("records")
    return Value.list_val([
        Value.map_val({k: _python_to_value(v) for k, v in row.items()})
        for row in rows
    ])
