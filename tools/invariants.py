"""Refuse the invariants that can be decided by reading one file at a time.

Issues #19 and #53. Rules cheap enough that there is no excuse for any of them
living only in a document, each one carrying a failure somebody has actually
shipped somewhere. What the set is at any moment is `RULES` below and is not
counted here, because a count in a docstring drifts against the tuple under it.

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

  no-unpinned-action
      #53. An action named by a tag is a name its owner can move under this
      repository between one run and the next, and the version comment beside
      the commit is what lets a reader tell which release they are looking at.

  no-write-permission-at-the-workflow-level
      #53. A write scope at the top of a file is granted to every job in it,
      including the ones that only read, so a step added later inherits a token
      nobody decided to give it. An absent block is refused too, because the
      default is then a repository setting rather than a property of the file.

  checkout-does-not-persist-credentials
      #53. A checkout that keeps the token leaves it in the job's git config,
      where any later step can push with it.

Most rules read a parsed document rather than the lines. That is a departure
from the word "greppable" in #19 and it is deliberate: a line-based pattern
refuses a float in a comment and misses one written in exponent form, and both
of those are worse than the rule not existing, because they teach people to
suppress it. The pinning rule is the exception and reads the line, because half
of what it wants is the version comment and a parser throws comments away.

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
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

import yaml

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
    # Which files the rule reads. "python" reads the parse tree of a .py file,
    # "workflow" reads a .yml file under .github/workflows/ as text and as
    # data. A rule reads one kind, because a rule that reads two is two rules.
    kind: str = "python"


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
    Rule(
        id="no-unpinned-action",
        prevents=(
            "an action referenced by a tag or a branch, which is a name its "
            "owner can move under this repository between one run and the next"
        ),
        subjects=(".github/workflows/",),
        kind="workflow",
    ),
    Rule(
        id="no-write-permission-at-the-workflow-level",
        prevents=(
            "a write scope granted to every job in a file, including the ones "
            "that only read, so a step added later inherits a token nobody "
            "decided to give it"
        ),
        subjects=(".github/workflows/",),
        kind="workflow",
    ),
    Rule(
        id="checkout-does-not-persist-credentials",
        prevents=(
            "a token left in the checkout's git config, where any later step "
            "in the job can push with it"
        ),
        subjects=(".github/workflows/",),
        kind="workflow",
    ),
)


# owner/repo@ref, with anything after it on the line kept so the version comment
# can be judged too. A local action, written ./path, is not a pinning question.
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<ref>\S+)(?P<rest>.*)$")
FORTY_HEX = re.compile(r"^[0-9a-f]{40}$")


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


def unpinned_action_offences(path: str, text: str) -> list[str]:
    """Every `uses:` reaches a commit and says beside it which release that is.

    Read from the line rather than from the parsed document, because half of
    what this rule wants is the comment and a parser throws comments away.
    """
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = USES.match(line)
        if match is None:
            continue
        reference = match.group("ref")
        if reference.startswith("."):
            continue  # a local action, which is this repository's own tree
        if "@" not in reference:
            found.append(f"{path}:{number}: {reference} names no revision at all")
            continue
        revision = reference.rsplit("@", 1)[1]
        if not FORTY_HEX.match(revision):
            found.append(f"{path}:{number}: {reference} is pinned to {revision!r}")
        elif "#" not in match.group("rest"):
            found.append(
                f"{path}:{number}: {reference} carries no version comment, so a "
                "reader cannot tell which release the commit is"
            )
    return found


def _write_scopes(permissions: object) -> list[str]:
    """The scopes in one `permissions:` value that grant more than reading."""
    if permissions is None:
        return []
    if isinstance(permissions, str):
        return [] if permissions == "read-all" else [permissions]
    if isinstance(permissions, dict):
        return [
            f"{scope}: {value}"
            for scope, value in sorted(permissions.items())
            if value not in {"read", "none"}
        ]
    return []


def workflow_permission_offences(path: str, text: str) -> list[str]:
    """The top-level `permissions:` block grants nothing that writes."""
    document = yaml.safe_load(text)
    if not isinstance(document, dict):
        return []
    if "permissions" not in document:
        # Absent is worse than a read-only block: the default is then whatever
        # the repository setting happens to be, which is not a property of this
        # file and can change without a diff.
        return [f"{path}: no permissions block at the workflow level"]
    scopes = _write_scopes(document["permissions"])
    return [f"{path}: the workflow level grants {scope}" for scope in scopes]


def checkout_credential_offences(path: str, text: str) -> list[str]:
    """Every checkout step drops the token it would otherwise leave behind."""
    document = yaml.safe_load(text)
    if not isinstance(document, dict):
        return []
    found = []
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return []
    for name, job in sorted(jobs.items()):
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if not isinstance(uses, str) or not uses.startswith("actions/checkout@"):
                continue
            settings = step.get("with")
            dropped = (
                isinstance(settings, dict)
                and settings.get("persist-credentials") is False
            )
            if not dropped:
                found.append(
                    f"{path}: job {name!r} step {index} checks out without "
                    "persist-credentials: false"
                )
    return found


PYTHON_OFFENCES: dict[str, Callable[[str, ast.AST], list[str]]] = {
    "no-float-above-the-boundary": float_offences,
    "no-networking-import": networking_offences,
    "no-catch-all-except": catch_all_offences,
    "no-fixture-outside-the-repository": outside_offences,
}

WORKFLOW_OFFENCES: dict[str, Callable[[str, str], list[str]]] = {
    "no-unpinned-action": unpinned_action_offences,
    "no-write-permission-at-the-workflow-level": workflow_permission_offences,
    "checkout-does-not-persist-credentials": checkout_credential_offences,
}

# Every rule id that has something behind it. The suite reads this rather than
# either dictionary, so a rule of a kind nobody wired up fails there.
OPERATOR_IDS = frozenset(PYTHON_OFFENCES) | frozenset(WORKFLOW_OFFENCES)


def kind_of(path: str) -> str:
    if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
        return "workflow"
    if path.endswith(".py"):
        return "python"
    return "unread"


def file_failures(path: str, text: str) -> list[str]:
    """Refusals for one file, as `rule-id: detail` lines."""
    kind = kind_of(path)
    applicable = [
        rule for rule in RULES if rule.kind == kind and rule_reads(rule, path)
    ]
    if not applicable:
        return []

    failures = []
    if kind == "python":
        try:
            tree = ast.parse(text, filename=path)
        except SyntaxError as broken:
            # Not a rule of its own. A file this checker cannot parse is a file
            # none of the rules read, and passing it silently is the one outcome
            # that must not happen.
            return [f"unparsable: {path}:{broken.lineno}: {broken.msg}"]
        for rule in applicable:
            for offence in PYTHON_OFFENCES[rule.id](path, tree):
                failures.append(f"{rule.id}: {offence}, which is {rule.prevents}")
        return failures

    try:
        yaml.safe_load(text)
    except yaml.YAMLError as broken:
        return [f"unparsable: {path}: {broken}"]
    for rule in applicable:
        for offence in WORKFLOW_OFFENCES[rule.id](path, text):
            failures.append(f"{rule.id}: {offence}, which is {rule.prevents}")
    return failures


def failures(files: Iterable[tuple[str, str]]) -> list[str]:
    found: list[str] = []
    for path, text in sorted(files):
        found.extend(file_failures(path, text))
    return found


def source_files(root: str) -> list[tuple[str, str]]:
    """Every file under the subjects the rules name that some rule can read."""
    wanted = sorted({subject for rule in RULES for subject in rule.subjects})
    found: list[tuple[str, str]] = []
    for subject in wanted:
        base = os.path.join(root, subject.replace("/", os.sep))
        if not os.path.isdir(base):
            continue
        for directory, names, filenames in os.walk(base):
            names[:] = [n for n in names if n not in {"__pycache__", ".venv"}]
            for filename in sorted(filenames):
                if not filename.endswith((".py", ".yml", ".yaml")):
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

    files = source_files(arguments.root)
    if not files:
        print(
            f"no readable file under the subjects the rules name, below "
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
