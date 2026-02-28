#!/usr/bin/env python3
"""
TinyTalk CLI
Run .tt files, start REPL, or transpile.

Usage:
    tinytalk run <file.tt>            Run a TinyTalk program
    tinytalk repl                     Start interactive REPL
    tinytalk check <file.tt>          Parse and report errors (no execution)
    tinytalk transpile <file.tt>      Transpile to Python
    tinytalk transpile-sql <file.tt>  Transpile to SQL
    tinytalk transpile-js <file.tt>   Transpile to JavaScript
    tinytalk init                     Initialize a new project (tiny.toml)
    tinytalk install <pkg> [--source] Install a package
    tinytalk deps                     Install all dependencies from tiny.toml
    tinytalk lsp                      Start the Language Server (stdio)
"""

import sys
import os


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__.strip())
        return

    cmd = args[0]

    if cmd == "run" and len(args) >= 2:
        run_file(args[1])
    elif cmd == "repl":
        start_repl()
    elif cmd == "check" and len(args) >= 2:
        check_file(args[1])
    elif cmd == "transpile" and len(args) >= 2:
        transpile_file(args[1])
    elif cmd in ("transpile-sql", "sql") and len(args) >= 2:
        transpile_sql_file(args[1])
    elif cmd in ("transpile-js", "js") and len(args) >= 2:
        transpile_js_file(args[1])
    elif cmd == "init":
        init_project()
    elif cmd == "install" and len(args) >= 2:
        install_package(args[1:])
    elif cmd == "deps":
        install_deps()
    elif cmd == "lsp":
        start_lsp()
    else:
        print(f"Unknown command: {cmd}")
        print("Use 'tinytalk help' for usage.")
        sys.exit(1)


def run_file(path: str):
    from .kernel import TinyTalkKernel

    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    with open(path, "r") as f:
        source = f.read()

    source_dir = os.path.dirname(os.path.abspath(path))
    kernel = TinyTalkKernel(capture_output=False, source_dir=source_dir)
    result = kernel.run(source)

    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        sys.exit(1)


def check_file(path: str):
    from .lexer import Lexer
    from .parser import Parser

    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    with open(path, "r") as f:
        source = f.read()

    try:
        tokens = Lexer(source).tokenize()
        Parser(tokens).parse()
        print(f"OK: {path} parsed successfully.")
    except SyntaxError as e:
        print(f"Syntax error in {path}: {e}")
        sys.exit(1)


def transpile_file(path: str):
    from .transpiler import transpile

    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    with open(path, "r") as f:
        source = f.read()

    print(transpile(source))


def transpile_sql_file(path: str):
    from .sql_transpiler import transpile_sql

    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    with open(path, "r") as f:
        source = f.read()

    print(transpile_sql(source))


def transpile_js_file(path: str):
    from .js_transpiler import transpile_js

    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    with open(path, "r") as f:
        source = f.read()

    print(transpile_js(source))


def start_repl():
    from .kernel import TinyTalkKernel
    TinyTalkKernel(capture_output=False).repl()


def init_project():
    from .package_manager import init_project as _init
    try:
        path = _init(".")
        print(f"Created {path}")
        print("Created main.tt")
        print("Created .tinytalk/packages/")
        print("\nReady! Run: tinytalk run main.tt")
    except FileExistsError:
        print("tiny.toml already exists in this directory.")
        sys.exit(1)


def install_package(args):
    from .package_manager import install_package as _install

    name = args[0]
    source = ""
    # Parse --source flag
    for i, a in enumerate(args[1:], 1):
        if a == "--source" and i + 1 < len(args):
            source = args[i + 1]
            break
        elif a.startswith("--source="):
            source = a.split("=", 1)[1]
            break

    if not source:
        source = name  # Default: treat name as source path

    try:
        path = _install(name, source)
        print(f"Installed '{name}' to {path}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def install_deps():
    from .package_manager import load_project_config, install_package as _install
    config = load_project_config(".")
    if not config:
        print("No tiny.toml found. Run 'tinytalk init' first.")
        sys.exit(1)
    if not config.dependencies:
        print("No dependencies in tiny.toml.")
        return
    for name, dep in config.dependencies.items():
        source = dep.source if dep.source else name
        try:
            path = _install(name, source)
            print(f"Installed '{name}' to {path}")
        except ValueError as e:
            print(f"Error installing '{name}': {e}")


def start_lsp():
    from .lsp_server import TinyTalkLSP
    server = TinyTalkLSP()
    server.start()


if __name__ == "__main__":
    main()
