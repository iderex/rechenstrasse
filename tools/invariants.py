"""Refuse the invariants that can be decided by reading one file at a time.

Issue #19. Four rules, each cheap enough that there is no excuse for it living
only in a document, and each one carrying a failure somebody has actually
shipped somewhere.

  no-float-above-the-boundary
      Record 0006 fixes one boundary, at evaluation, and says modules above it
      may not name a float literal. A float above it is not loud: it does not
      raise, it does not usually move the first digits, and it changes whether
      two expressions that should be equal subtract to zero. That is the
      comparison this board rests on.

  no-networking-import
      Nothing this pipeline computes leaves the host, which is #54 and record
      0056. An import is where that stops being true, and it is one line in a
      diff nobody is looking at.

  no-catch-all-except
      The admissibility gate of #26 refuses by returning a value and by an exit
      status, and a catch-all around a stage turns a refusal into a shrug. The
      failure is not the crash, it is the run that continues and prints a
      number.

  no-fixture-outside-the-repository
      Record 0009 says a test runs on a machine with nothing installed beyond
      the pinned toolchain. A test that reads an absolute path or somebody's
      home directory passes on one workstation and is then quietly skipped by
      everybody else.

The rules read the parse tree rather than the lines. That is a departure from
the word "greppable" in the issue and it is deliberate: a line-based pattern
refuses a float in a comment and misses one written in exponent form, and both
of those are worse than the rule not existing, because they teach people to
suppress it. The parse tree comes from the standard library and costs nothing.

Every rule has two lists beside it, of paths it is allowed to skip. Both are
empty today. They are read by the suite, which refuses an entry naming a path
that is not in the tree, so an exemption cannot outlive the file it was written
for.

    python tools/invariants.py
"""

import argparse
import ast
import os
import re
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

# Modules that reach the network. Not a complete list of every way a process can
# open a socket, and not claimed to be one: it holds what a stage in this
# pipeline would plausibly import, and the rule is a floor rather than a
# guarantee.
NETWORKING_MODULES = frozenset(
    {
        "asyncio",
        "ftplib",
        "http",
        "httpx",
        "imaplib",
        "poplib",
        "requests",
        "smtplib",
        "socket",
        "socketserver",
        "ssl",
        "urllib",
        "urllib3",
        "webbrowser",
        "xmlrpc",
    }
)

# Catching either of these catches a refusal along with everything else.
CATCH_ALL = frozenset({"Exception", "BaseException"})

# A POSIX absolute path or a Windows drive path, written as a literal.
ABSOLUTE_PATH = re.compile(r"^(/[^\s/][^\n]*|[A-Za-z]:[\\/][^\n]*)$")

# Reaching for a directory that belongs to whoever ran the test.
OUTSIDE_CALLS = frozenset({"expanduser", "home", "expandvars", "gethostname"})


@dataclass(frozen=True)
class Rule:
    """One invariant, the files it reads, and the files it is allowed to skip."""

    id: str
    prevents: str
    # Path prefixes the rule reads, relative to the repository root, with
    # forward slashes.
    subjects: tuple[str, ...]
    # Exact paths the rule does not read. Every entry has to exist in the tree,
    # which the suite refuses a violation of, so a waiver cannot outlive its
    # file.
    exempt: tuple[str, ...] = field(default=())
    # True where the rule reads only test files inside its subjects.
    tests_only: bool = False


RULES: tuple[Rule, ...] = (
    Rule(
        id="no-float-above-the-boundary",
        prevents=(
            "a float literal in a module above the evaluation boundary, which "
            "turns an exact comparison against a published expression into one "
            "that needs a tolerance"
        ),
        subjects=("src/rechenstrasse/",),
    ),
    Rule(
        id="no-networking-import",
        prevents=(
            "an import that can reach the network, in a tree whose promise is "
            "that what an operator computes stays on the host"
        ),
        subjects=("src/", "tools/", ".github/pr-hygiene/"),
    ),
    Rule(
        id="no-catch-all-except",
        prevents=(
            "a catch-all around a stage, which turns a refusal from the "
            "admissibility gate into a run that continues and prints a number"
        ),
        subjects=("src/", "tools/", ".github/pr-hygiene/"),
    ),
    Rule(
        id="no-fixture-outside-the-repository",
        prevents=(
            "a test that reads an absolute path or a home directory, which "
            "passes on the machine it was written on and nowhere else"
        ),
        subjects=("src/", "tools/", ".github/pr-hygiene/"),
        tests_only=True,
    ),
)


def is_test_file(path: str) -> bool:
    name = os.path.basename(path)
    return name.startswith("test_") or name.endswith("_test.py")


def rule_reads(rule: Rule, path: str) -> bool:
    if path in rule.exempt:
        return False
    if rule.tests_only and not is_test_file(path):
        return False
    return any(path.startswith(subject) for subject in rule.subjects)


def _dotted_root(name: str) -> str:
    return name.split(".", 1)[0]


def float_offences(path: str, tree: ast.AST) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            found.append(f"{path}:{node.lineno}: the float literal {node.value!r}")
    return found


def networking_offences(path: str, tree: ast.AST) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _dotted_root(alias.name) in NETWORKING_MODULES:
                    found.append(f"{path}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            if _dotted_root(node.module) in NETWORKING_MODULES:
                found.append(f"{path}:{node.lineno}: from {node.module} import ...")
    return found


def catch_all_offences(path: str, tree: ast.AST) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if node.type is None:
            found.append(f"{path}:{node.lineno}: a bare except")
        elif isinstance(node.type, ast.Name) and node.type.id in CATCH_ALL:
            found.append(f"{path}:{node.lineno}: except {node.type.id}")
    return found


def outside_offences(path: str, tree: ast.AST) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if ABSOLUTE_PATH.match(node.value):
                found.append(f"{path}:{node.lineno}: the absolute path {node.value!r}")
        elif isinstance(node, ast.Attribute) and node.attr in OUTSIDE_CALLS:
            found.append(f"{path}:{node.lineno}: a call to {node.attr}")
    return found


OFFENCES = {
    "no-float-above-the-boundary": float_offences,
    "no-networking-import": networking_offences,
    "no-catch-all-except": catch_all_offences,
    "no-fixture-outside-the-repository": outside_offences,
}


def file_failures(path: str, text: str) -> list[str]:
    """Refusals for one file, as `rule-id: detail` lines."""
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as broken:
        # Not a rule of its own. A file this checker cannot parse is a file none
        # of the four rules read, and passing it silently is the one outcome
        # that must not happen.
        return [f"unparsable: {path}:{broken.lineno}: {broken.msg}"]

    failures = []
    for rule in RULES:
        if not rule_reads(rule, path):
            continue
        for offence in OFFENCES[rule.id](path, tree):
            failures.append(f"{rule.id}: {offence}, which is {rule.prevents}")
    return failures


def failures(files: Iterable[tuple[str, str]]) -> list[str]:
    found: list[str] = []
    for path, text in sorted(files):
        found.extend(file_failures(path, text))
    return found


def python_files(root: str) -> list[tuple[str, str]]:
    """Every tracked-looking Python file under the subjects the rules name."""
    wanted = sorted({subject for rule in RULES for subject in rule.subjects})
    found: list[tuple[str, str]] = []
    for subject in wanted:
        base = os.path.join(root, subject.replace("/", os.sep))
        if not os.path.isdir(base):
            continue
        for directory, names, filenames in os.walk(base):
            names[:] = [n for n in names if n not in {"__pycache__", ".venv"}]
            for filename in sorted(filenames):
                if not filename.endswith(".py"):
                    continue
                full = os.path.join(directory, filename)
                relative = os.path.relpath(full, root).replace(os.sep, "/")
                if any(relative == path for path, _ in found):
                    continue
                with open(full, encoding="utf-8") as handle:
                    found.append((relative, handle.read()))
    return found


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refuse the invariants one file can decide on its own."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
        help="the repository root to read",
    )
    arguments = parser.parse_args(argv)

    files = python_files(arguments.root)
    if not files:
        print(
            f"no Python under the subjects the rules name, below "
            f"{arguments.root}, which is either the wrong root or a tree that "
            "lost its source",
            file=sys.stderr,
        )
        return 1

    found = failures(files)
    for failure in found:
        print(failure, file=sys.stderr)
    if found:
        print(
            f"{len(found)} refusal(s) over {len(files)} file(s)",
            file=sys.stderr,
        )
        return 1
    print(f"{len(RULES)} invariant(s) over {len(files)} file(s), nothing refused")
    return 0


if __name__ == "__main__":
    sys.exit(main())
