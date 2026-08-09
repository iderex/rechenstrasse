"""The default suite imports nothing from the second harness.

Issue #65, and record 0009 behind it. The harness holds work a plain runner
cannot do. The moment a module the default run imports reaches into it, the
default run inherits that requirement, and the first machine without a
canonicalisation core turns red on a suite that is supposed to need nothing.

Read from the parse tree rather than by importing anything, so a module that
would fail to import for its own reasons is still judged, and so this leg needs
no environment beyond the tree it walks. It is fast: it reads the files the
default run and the package are made of and starts no second process, which is
why it is not marked slow.

The dependency is allowed to run the other way. The harness imports the package,
because exercising it is the whole point.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The package whose name may not appear in an import above it.
HARNESS = "native_or_long"

# What the default run reads, and the package it exercises. Both, because a stage
# importing the harness is worse than a test doing it: it puts the requirement
# into the pipeline itself.
READ = ("tests", "src")


def python_files() -> list[Path]:
    found: list[Path] = []
    for directory in READ:
        found.extend(sorted((ROOT / directory).rglob("*.py")))
    return found


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".", 1)[0])
    return roots


def test_nothing_the_default_run_reads_imports_the_harness() -> None:
    files = python_files()
    assert files, "the walk found no source, which is a broken test and not a pass"
    offences = [
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in files
        if HARNESS in imported_roots(ast.parse(path.read_text(encoding="utf-8")))
    ]
    assert offences == [], (
        f"these files import {HARNESS}, which puts the harness's requirements "
        f"into the default run: {offences}"
    )


def test_the_walk_would_see_such_an_import() -> None:
    # The near miss, and the reason the leg above is not vacuous. A guard that
    # reads the wrong thing reports the same empty list forever.
    seen = imported_roots(ast.parse(f"from {HARNESS} import seam\n"))
    assert HARNESS in seen
    assert imported_roots(ast.parse("import rechenstrasse\n")) == {"rechenstrasse"}


def test_the_harness_is_in_the_tree_to_be_imported() -> None:
    # A guard that passes because its subject went away is a guard that stopped
    # working. If the harness is renamed, this is what says so.
    assert (ROOT / HARNESS / "__init__.py").is_file()
