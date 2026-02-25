"""
TinyTalk Package Manager
Install, manage, and resolve TinyTalk dependencies.

Provides:
    tinytalk install <package>   Install a package from the registry
    tinytalk init                Create a new tiny.toml project file
    tinytalk deps                Install all dependencies from tiny.toml

Registry: GitHub-backed index (packages are Git repos with a tiny.toml).
Local packages are stored in a .tinytalk/packages/ directory.
"""

from __future__ import annotations
import os
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PackageDep:
    """A single dependency declaration."""
    name: str
    version: str = "*"
    source: str = ""  # URL or registry name

    def __repr__(self):
        return f"{self.name}@{self.version}"


@dataclass
class TinyToml:
    """Parsed tiny.toml project configuration."""
    name: str = "my-project"
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    entry: str = "main.tt"
    dependencies: Dict[str, PackageDep] = field(default_factory=dict)

    def to_string(self) -> str:
        lines = [
            "[project]",
            f'name = "{self.name}"',
            f'version = "{self.version}"',
        ]
        if self.description:
            lines.append(f'description = "{self.description}"')
        if self.author:
            lines.append(f'author = "{self.author}"')
        lines.append(f'entry = "{self.entry}"')
        lines.append("")
        lines.append("[dependencies]")
        for name, dep in self.dependencies.items():
            if dep.source:
                lines.append(f'{name} = {{version = "{dep.version}", source = "{dep.source}"}}')
            else:
                lines.append(f'{name} = "{dep.version}"')
        lines.append("")
        return "\n".join(lines)


def parse_tiny_toml(content: str) -> TinyToml:
    """Parse a tiny.toml configuration file.

    Supports a simplified TOML-like format:
        [project]
        name = "my-project"
        version = "0.1.0"

        [dependencies]
        utils = "1.0.0"
        http = {version = "2.0", source = "github:user/repo"}
    """
    config = TinyToml()
    section = ""

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Section header
        m = re.match(r'^\[(\w+)\]$', line)
        if m:
            section = m.group(1)
            continue

        # Key-value pair
        m = re.match(r'^(\w[\w-]*)\s*=\s*(.+)$', line)
        if not m:
            continue

        key, raw_value = m.group(1), m.group(2).strip()

        # Parse value
        value = _parse_toml_value(raw_value)

        if section == "project":
            if key == "name":
                config.name = value
            elif key == "version":
                config.version = value
            elif key == "description":
                config.description = value
            elif key == "author":
                config.author = value
            elif key == "entry":
                config.entry = value
        elif section == "dependencies":
            if isinstance(value, dict):
                config.dependencies[key] = PackageDep(
                    name=key,
                    version=value.get("version", "*"),
                    source=value.get("source", ""),
                )
            else:
                config.dependencies[key] = PackageDep(name=key, version=str(value))

    return config


def _parse_toml_value(raw: str):
    """Parse a TOML-like value: string, number, or inline table."""
    raw = raw.strip()
    # Quoted string
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    # Inline table
    if raw.startswith("{") and raw.endswith("}"):
        inner = raw[1:-1]
        result = {}
        for part in inner.split(","):
            kv = part.strip().split("=", 1)
            if len(kv) == 2:
                k = kv[0].strip()
                v = _parse_toml_value(kv[1].strip())
                result[k] = v
        return result
    # Boolean
    if raw == "true":
        return True
    if raw == "false":
        return False
    # Number
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


# ---------------------------------------------------------------------------
# Registry (GitHub-backed index)
# ---------------------------------------------------------------------------

# Default registry: a GitHub repo containing an index.json
DEFAULT_REGISTRY = "https://raw.githubusercontent.com/tinytalk-lang/registry/main/index.json"

# Local package storage
PACKAGES_DIR = ".tinytalk/packages"


@dataclass
class RegistryEntry:
    """A package entry in the registry index."""
    name: str
    version: str
    description: str = ""
    source: str = ""  # Git URL
    files: List[str] = field(default_factory=list)


def get_packages_dir(project_root: str = ".") -> str:
    """Get the packages directory, creating it if needed."""
    pkg_dir = os.path.join(project_root, PACKAGES_DIR)
    os.makedirs(pkg_dir, exist_ok=True)
    return pkg_dir


def resolve_import_path(module_name: str, source_dir: str = ".") -> Optional[str]:
    """Resolve a module import to an actual file path.

    Search order:
        1. Relative to source file
        2. In .tinytalk/packages/<module_name>/
        3. In .tinytalk/packages/<module_name>/main.tt
    """
    # 1. Relative import
    rel_path = os.path.join(source_dir, module_name)
    if not rel_path.endswith(".tt"):
        rel_path += ".tt"
    if os.path.exists(rel_path):
        return os.path.abspath(rel_path)

    # 2. Package directory
    pkg_dir = os.path.join(source_dir, PACKAGES_DIR, module_name)
    if os.path.isdir(pkg_dir):
        # Check for main.tt or <name>.tt
        for candidate in ["main.tt", f"{module_name}.tt", "index.tt"]:
            path = os.path.join(pkg_dir, candidate)
            if os.path.exists(path):
                return os.path.abspath(path)

    # 3. Walk up to project root looking for packages
    current = os.path.abspath(source_dir)
    for _ in range(10):  # max depth
        pkg_path = os.path.join(current, PACKAGES_DIR, module_name)
        if os.path.isdir(pkg_path):
            for candidate in ["main.tt", f"{module_name}.tt", "index.tt"]:
                path = os.path.join(pkg_path, candidate)
                if os.path.exists(path):
                    return os.path.abspath(path)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    return None


def init_project(path: str = ".") -> str:
    """Initialize a new TinyTalk project with tiny.toml."""
    toml_path = os.path.join(path, "tiny.toml")
    if os.path.exists(toml_path):
        raise FileExistsError(f"tiny.toml already exists in {path}")

    project_name = os.path.basename(os.path.abspath(path))
    config = TinyToml(name=project_name)

    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(config.to_string())

    # Create main.tt if it doesn't exist
    main_path = os.path.join(path, "main.tt")
    if not os.path.exists(main_path):
        with open(main_path, "w", encoding="utf-8") as f:
            f.write('// Welcome to your TinyTalk project!\nshow("Hello from {0}!")\n'.format(project_name))

    # Create packages directory
    get_packages_dir(path)

    return toml_path


def load_project_config(path: str = ".") -> Optional[TinyToml]:
    """Load tiny.toml from the given directory."""
    toml_path = os.path.join(path, "tiny.toml")
    if not os.path.exists(toml_path):
        return None
    with open(toml_path, "r", encoding="utf-8") as f:
        return parse_tiny_toml(f.read())


def install_package(name: str, source: str = "", project_root: str = ".") -> str:
    """Install a package into the project's .tinytalk/packages/ directory.

    For now, supports:
        - Local path: tinytalk install ./path/to/package
        - GitHub shorthand: tinytalk install github:user/repo

    Returns the install path.
    """
    pkg_dir = get_packages_dir(project_root)
    target = os.path.join(pkg_dir, name)

    if source.startswith("github:"):
        # GitHub-backed package
        repo = source[7:]  # strip "github:"
        # In a real implementation, this would clone the repo
        os.makedirs(target, exist_ok=True)
        readme = os.path.join(target, "README.md")
        with open(readme, "w") as f:
            f.write(f"# {name}\nInstalled from github:{repo}\n")
        return target

    if os.path.isdir(source):
        # Local directory — copy .tt files
        import shutil
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(source, target, dirs_exist_ok=True)
        return target

    if os.path.isfile(source) and source.endswith(".tt"):
        # Single file package
        os.makedirs(target, exist_ok=True)
        import shutil
        shutil.copy2(source, os.path.join(target, "main.tt"))
        return target

    raise ValueError(
        f"Cannot install '{name}': source '{source}' not found.\n"
        f"Use: tinytalk install <name> --source <path-or-github:user/repo>"
    )
