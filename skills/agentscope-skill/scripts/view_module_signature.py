# -*- coding: utf-8 -*-
"""Inspect installed AgentScope APIs without importing every integration."""
import argparse
import importlib
import inspect
import pkgutil
import sys
from types import ModuleType
from typing import Any


def resolve_target(path: str) -> Any:
    """Import the requested module, then resolve class or method attributes."""
    parts = path.split(".")
    if parts[0] != "agentscope" or not all(p.isidentifier() for p in parts):
        raise ValueError("Use 'agentscope' or a dotted path below it.")

    target: Any = importlib.import_module("agentscope")
    for index, name in enumerate(parts[1:], start=1):
        if isinstance(target, ModuleType):
            module_name = ".".join(parts[: index + 1])
            try:
                target = importlib.import_module(module_name)
                continue
            except ModuleNotFoundError as exc:
                # Missing dependencies inside a real module are not a missing
                # target; preserve that error so the user can install extras.
                if exc.name != module_name:
                    raise
        target = getattr(target, name)
    return target


def source_reference(target: Any) -> str:
    """Return a source location when Python can locate the implementation."""
    try:
        source = inspect.getsourcefile(target)
        _, line = inspect.getsourcelines(target)
        return f"{source}:{line}"
    except (OSError, TypeError):
        return "Source unavailable (built-in or generated object)."


def callable_signature(target: Any) -> str:
    """Render a callable, preserving async and async-generator markers."""
    prefix = (
        "async def"
        if (
            inspect.iscoroutinefunction(target)
            or inspect.isasyncgenfunction(target)
        )
        else "def"
    )
    try:
        signature = str(inspect.signature(target))
    except (TypeError, ValueError):
        signature = " (signature unavailable)"
    return f"{prefix} {target.__name__}{signature}"


def describe_class(target: type) -> str:
    """Describe a class, including inherited public methods and fields."""
    lines = [f"class {target.__name__}{inspect.signature(target)}"]
    if inspect.getdoc(target):
        lines.append(inspect.getdoc(target) or "")
    lines.append(f"Source: {source_reference(target)}")
    for name, member in inspect.getmembers(target):
        if name.startswith("_") and name not in {"__init__", "__call__"}:
            continue
        if inspect.isroutine(member):
            owner = next(
                (
                    base.__name__
                    for base in target.__mro__
                    if name in vars(base)
                ),
                target.__name__,
            )
            lines.append(
                f"\n{callable_signature(member)} [defined on {owner}]",
            )
            if inspect.getdoc(member):
                lines.append(inspect.getdoc(member) or "")
    return "\n".join(lines)


def describe_module(target: ModuleType) -> str:
    """List exports and child modules without loading optional integrations."""
    lines = [inspect.getdoc(target) or target.__name__]
    package_path = vars(target).get("__path__")
    if package_path is not None:
        children = sorted(
            item.name
            for item in pkgutil.iter_modules(package_path)
            if not item.name.startswith("_")
        )
        lines.extend(f"- module {target.__name__}.{name}" for name in children)

    namespace = vars(target)
    names = namespace.get("__all__", sorted(namespace))
    for name in names:
        if name.startswith("_"):
            continue
        qualified_name = f"{target.__name__}.{name}"
        if name not in namespace:
            lines.append(f"- {qualified_name} (lazy export; inspect directly)")
            continue
        member = namespace[name]
        if inspect.isclass(member) or inspect.isroutine(member):
            doc = inspect.getdoc(member) or ""
            lines.append(
                f"- {qualified_name}: {doc.splitlines()[0] if doc else ''}",
            )
    lines.append(
        "Inspect a dotted class or method path for its full signature.",
    )
    return "\n".join(lines)


def view_agentscope_library(module: str) -> str:
    """Show the installed version, location, and requested public API."""
    target = resolve_target(module)
    package = importlib.import_module("agentscope")
    header = (
        f"AgentScope {getattr(package, '__version__', 'unknown')}\n"
        f"Loaded from: {package.__file__}\n\n"
    )
    if inspect.ismodule(target):
        body = describe_module(target)
    elif inspect.isclass(target):
        body = describe_class(target)
    elif inspect.isroutine(target):
        body = (
            f"{callable_signature(target)}\n"
            f"{inspect.getdoc(target) or ''}\n"
            f"Source: {source_reference(target)}"
        )
    else:
        body = repr(target)
    return header + body


def main() -> int:
    """Run the command-line inspector with actionable import errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", default="agentscope")
    args = parser.parse_args()
    try:
        print(view_agentscope_library(args.module))
    except (ImportError, AttributeError, ValueError, TypeError) as exc:
        print(
            f"Cannot inspect {args.module}: {exc}\n"
            "Check the target path, active environment, and the optional "
            "dependencies in the target AgentScope pyproject.toml.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
