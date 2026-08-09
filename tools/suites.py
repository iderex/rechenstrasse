"""What a default run of the suite did not run, and the command for each.

Issue #15. A run says what it examined. The default run is the fast half of
`tests/`, and this tree holds other suites it never touches. What they are is the
list below rather than a sentence here, which would drift against it. They are
printed by name at the end of a run together with the command that would run
each, so a green result cannot be read as covering more than it did.

The list is data in the tree rather than an echo inside a workflow file, for two
reasons. A list written into a job is a list nothing can test, and this one has
to fail closed in both directions:

  a dangling entry
      An entry naming a file that is not in the tree, or covering a directory
      that holds no test file. The suite it describes either moved or went away,
      and either way the disclosure is now telling a reader about something that
      does not exist.

  an undisclosed suite
      A test file outside the directory the default run reads, or a test file
      inside it carrying the marker that deselects it, which no entry names and
      no entry covers. That is the drift this file exists against: a suite
      arrives, the default run does not run it, and nothing says so.

Both are refused by `failures` below, which `main` runs before it prints, so the
disclosure cannot go stale without the check that prints it going red.

What this does not do, said plainly so the guard is not read as more than it is.
It reads paths and it greps for the marker; it does not ask pytest's collector
which tests would be selected. A test left out of the default run for any other
reason than that marker is outside it, and so is a suite that exists in no file
matching a test file name.

    python tools/suites.py
"""

import argparse
import os
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

# The directory the default run reads, from `testpaths` in pyproject.toml. A test
# file outside it is a file the default run never sees, whatever it is called.
DEFAULT_RUN = "tests/"

# The marker that takes a test out of the default run, from `addopts` in
# pyproject.toml. Read as text rather than from a collection, which is the bound
# the docstring above states.
SLOW_MARKER = "pytest.mark.slow"


@dataclass(frozen=True)
class Suite:
    """One suite the default run leaves out, and the command that runs it."""

    name: str
    command: str
    # Every file the command runs, relative to the repository root, with forward
    # slashes. Each one has to be a test file in the tree.
    paths: tuple[str, ...]
    # Why the default run leaves it out. Printed with the entry, because a
    # reader deciding whether to run it needs the reason and not only the name.
    because: str
    # Directory prefixes the command runs whole, for an entry that is a suite
    # rather than a file. At least one test file has to sit under each prefix, so
    # a prefix cannot outlive the directory it was written for, and a file added
    # under one needs no edit here. Exact paths are the better form where the
    # entry is one file, because they say which file.
    covers: tuple[str, ...] = ()


SUITES: tuple[Suite, ...] = (
    Suite(
        name="the native-or-long harness",
        command="uv run pytest -rs native_or_long",
        paths=(),
        covers=("native_or_long/",),
        because=(
            "record 0009 puts work that needs a canonicalisation core compiled "
            "for this machine, or a derivation nobody would sit through, in a "
            "harness of its own, and a case in it that this machine cannot run "
            "is skipped with its reason printed rather than passed"
        ),
    ),
    Suite(
        name="the slow half of this suite",
        command="uv run pytest -q -m slow",
        paths=(
            "tests/test_tree_wide_checks.py",
            "tests/rechenstrasse/test_refusal.py",
        ),
        because=(
            "it starts a second interpreter and walks every file the invariants "
            "rules read, which is not something to sit through on every change"
        ),
    ),
    Suite(
        name="the decision record rule's own proof",
        command="uv run python tools/test_decision_records.py",
        paths=("tools/test_decision_records.py",),
        because=(
            "it is a standard library suite the `lint` check runs beside the "
            "rule it proves, and pytest never reads it"
        ),
    ),
    Suite(
        name="the checks-table rule's own proof",
        command="uv run python tools/test_checks_table.py",
        paths=("tools/test_checks_table.py",),
        because=(
            "it is a unittest suite the `lint` check runs beside the rule it "
            "proves, and pytest never reads it"
        ),
    ),
    Suite(
        name="the third party notice rule's own proof",
        command="uv run python tools/test_third_party_notices.py",
        paths=("tools/test_third_party_notices.py",),
        because=(
            "it is a standard library suite the `lint` check runs beside the "
            "rule it proves, and pytest never reads it"
        ),
    ),
    Suite(
        name="the invariants rules' own proof",
        command="uv run python tools/test_invariants.py",
        paths=("tools/test_invariants.py",),
        because=(
            "it is a standard library suite the `Enforce greppable invariants` "
            "check runs beside the rules it proves, and pytest never reads it"
        ),
    ),
    Suite(
        name="this disclosure's own proof",
        command="uv run python tools/test_suites.py",
        paths=("tools/test_suites.py",),
        because=(
            "it is run by this check before the list is printed, and pytest "
            "never reads it either"
        ),
    ),
    Suite(
        name="the pull request hygiene suite",
        command="python3 .github/pr-hygiene/test_hygiene.py",
        paths=(".github/pr-hygiene/test_hygiene.py",),
        because=(
            "it is a self-contained standard library module outside the "
            "environment this suite runs in, with a check of its own"
        ),
    ),
)

# Files that read as a test file and are not a suite. Every entry is an exact
# path and never a directory, and each one has to be in the tree, so an
# exemption cannot outlive the file it was written for.
NOT_A_SUITE: tuple[tuple[str, str], ...] = (
    (
        "fixtures/only_a_failing_test.py",
        "a fixture that exists to be refused, run by the step that proves the "
        "`tests` check reports a failing suite and by nothing else",
    ),
)

# Directories no walk of this tree has any business reading.
UNREAD = frozenset({".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"})


def is_test_file(path: str) -> bool:
    name = os.path.basename(path)
    return name.startswith("test_") or name.endswith("_test.py")


def test_files(root: str) -> list[tuple[str, str]]:
    """Every file in the tree whose name says it holds tests, with its text."""
    found: list[tuple[str, str]] = []
    for directory, names, filenames in os.walk(root):
        names[:] = [name for name in names if name not in UNREAD]
        for filename in sorted(filenames):
            if not filename.endswith(".py") or not is_test_file(filename):
                continue
            full = os.path.join(directory, filename)
            relative = os.path.relpath(full, root).replace(os.sep, "/")
            with open(full, encoding="utf-8") as handle:
                found.append((relative, handle.read()))
    return sorted(found)


def failures(files: Iterable[tuple[str, str]]) -> list[str]:
    """Refusals for one tree, as `kind: detail` lines.

    A pure function of the files it is given, so the suite can hand it a tree
    that is one file away from this one rather than having to plant a file in
    the real tree to find out what the disclosure would say about it.
    """
    present = {path for path, _ in files}
    prefixes = tuple(prefix for suite in SUITES for prefix in suite.covers)
    disclosed = {path for suite in SUITES for path in suite.paths}
    exempt = {path for path, _ in NOT_A_SUITE}

    found: list[str] = []
    for suite in SUITES:
        for path in sorted(set(suite.paths)):
            if path not in present:
                found.append(
                    f"dangling: {suite.name} names {path}, which is not a test "
                    "file in this tree, so the disclosure describes a suite "
                    "that moved or went away"
                )
        for prefix in sorted(set(suite.covers)):
            if not any(path.startswith(prefix) for path in present):
                found.append(
                    f"dangling: {suite.name} covers {prefix}, where this tree "
                    "holds no test file at all, so the disclosure describes a "
                    "suite that moved or went away"
                )
    for path, reason in sorted(NOT_A_SUITE):
        if path not in present:
            found.append(
                f"dangling: the exemption for {path} names no test file in this "
                f"tree, and it was written for one ({reason})"
            )

    for path, text in sorted(files):
        if path in disclosed or path in exempt or path.startswith(prefixes):
            continue
        if not path.startswith(DEFAULT_RUN):
            found.append(
                f"undisclosed: {path} holds tests the default run never reads, "
                "because it sits outside the directory that run is given, and "
                "no entry names it"
            )
        elif SLOW_MARKER in text:
            found.append(
                f"undisclosed: {path} carries the marker the default run "
                "deselects, and no entry names it"
            )
    return found


def report() -> str:
    """The disclosure itself, which is what a reader of a green run takes away."""
    lines = ["what this run did not run, and what would run it:"]
    for suite in SUITES:
        lines.append(f"  {suite.name}, because {suite.because}")
        lines.append(f"      {suite.command}")
    for path, reason in NOT_A_SUITE:
        lines.append(f"  not a suite: {path}, {reason}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Say which suites a default run did not run, and refuse a "
        "disclosure that has drifted from the tree."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
        help="the repository root to read",
    )
    arguments = parser.parse_args(argv)

    files = test_files(arguments.root)
    if not files:
        print(
            f"no file holding tests below {arguments.root}, which is either the "
            "wrong root or a tree that lost its suite",
            file=sys.stderr,
        )
        return 1

    found = failures(files)
    for failure in found:
        print(failure, file=sys.stderr)
    if found:
        print(
            f"{len(found)} refusal(s) over {len(files)} file(s) holding tests",
            file=sys.stderr,
        )
        return 1
    print(report())
    return 0


if __name__ == "__main__":
    sys.exit(main())
