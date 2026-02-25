"""Vercel serverless entry point — wraps the Flask app."""
import sys
import os
import importlib.util

# The repo root (parent of api/) contains all package modules.
# Register it as the "newTinyTalk" package so relative imports work.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

spec = importlib.util.spec_from_file_location(
    "newTinyTalk",
    os.path.join(ROOT, "__init__.py"),
    submodule_search_locations=[ROOT],
)
pkg = importlib.util.module_from_spec(spec)
sys.modules["newTinyTalk"] = pkg
spec.loader.exec_module(pkg)

from newTinyTalk.server import app  # noqa: E402
