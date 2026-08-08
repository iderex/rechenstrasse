"""Hold the table of checks in CONTRIBUTING.md against the workflows in the tree.

Issue #86. A first-time contributor meets a red name on a pull request and looks
it up in that table to find the command that decides the same thing in a clone.
Nothing read the table, so a check renamed, added or removed left the row stale
and every route stayed green. That is the drift a list written in a document
always has, and this tree already refuses two of its own instances rather than
trusting prose: `tools/suites.py` over the disclosure of what a run did not run,
and `tools/invariants.py` over the rules it keeps beside the code that decides
them.

The rules, and each fails closed against the tree:

  stale-row
      A row naming a check no workflow in this tree produces on a pull request.
      The row describes something that does not run, which is worse than no row
      at all: a contributor looks for a red name that will never appear.

  unnamed-check
      A check a workflow produces on a pull request that no row names. This is
      the direction with the cost. A check arrives, a contributor meets it red,
      and the document that was supposed to tell them what it is does not
      mention it.

  dangling-exception
      An entry in the register below naming a check a workflow in this tree now
      produces. The exception was written for a check that comes from somewhere
      else, and it has stopped being true.

  unused-exception
      An entry in the register naming no row in the table. It is describing a
      row that went away.

  undecidable-workflow
      A job whose check name this file cannot derive from the tree. Refused
      rather than guessed, because a name that looks right and is not sends a
      reader to a row that does not match what they saw.

The names are derived from a parsed document and never from the lines. A check
run takes its name from `jobs.<id>.name` where the job carries one and from the
job's own id where it does not, and a matrix job carries the combination in
parentheses after it. That last part is measured rather than assumed: the
`Locked environment restores` job in `.github/workflows/toolchain.yml` sets a
fixed name and the pull request shows it three times with the operating system
appended, one per matrix value.

What this does not do, said plainly so the guard is not read as more than it is.
It asks whether a workflow declares a `pull_request` trigger and never whether
that trigger fires for a given diff, so a `paths` or `branches` filter is not
evaluated: a check that appears on some pull requests and not others still owes
a row, which is the direction a contributor needs. It reads no network, so a
check reported by something other than a workflow in this tree is invisible to
it and is what the register below is for. And it is a check about names, not
about the second column: whether the command beside a row decides the same thing
the check decides is a judgement no reading of this tree makes.

    python tools/checks_table.py
"""

import argparse
import os
import re
import sys
from collections.abc import Callable, Iterable, Sequence

import yaml

# The document holding the table, and the directory holding the workflows. Both
# are paths relative to the repository root this command is given.
TABLE_DOCUMENT = "CONTRIBUTING.md"
WORKFLOW_DIRECTORY = ".github/workflows"

# The heading of the first column, which is what anchors the table. Anchored on
# the column title rather than on the section heading above it, because the
# title is the part that says what the column holds, and a document with no such
# column is refused rather than read as a table with no rows.
FIRST_COLUMN = "On the pull request"

# A cell holding exactly one backticked string and nothing else. The names carry
# spaces and parentheses, so the backticks are what says where the name ends.
NAME_CELL = re.compile(r"^`([^`]+)`$")

# A workflow expression. Anything still carrying one after the matrix values are
# substituted is a name this file cannot resolve from the tree.
EXPRESSION = re.compile(r"\$\{\{")

# A matrix reference inside a job name, which the server substitutes rather than
# appending the combination after it.
MATRIX_REFERENCE = re.compile(r"\$\{\{\s*matrix\.([A-Za-z_][A-Za-z0-9_-]*)\s*\}\}")

# Checks that appear on a pull request and that no workflow in this tree names,
# with what each one is. Every entry has to still be true in both directions:
# the check may not be produced by a workflow here, and a row in the table has
# to name it. An exemption that outlives either half is refused above.
NOT_FROM_A_WORKFLOW: tuple[tuple[str, str], ...] = (
    (
        "zizmor",
        "reported by code scanning once the `Audit workflows (zizmor)` job "
        "uploads its results, so it exists on a pull request while no workflow "
        "file in this tree carries that string as a name",
    ),
    (
        "CodeQL",
        "reported by code scanning once the `Analyze (python)` job uploads its "
        "results, the same shape as the entry above and found the same way, by "
        "reading the check names off a pull request rather than off this tree",
    ),
)


def table_names(text: str) -> tuple[list[str], list[str]]:
    """The first column of the table of checks, and refusals about the table.

    Returns the names in the order the document lists them. A document with no
    such table returns no names and one refusal, so a renamed column heading
    cannot read as a table that happens to be empty.
    """
    rows: list[str] = []
    found: list[str] = []
    inside = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            inside = False
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if cells[0] == FIRST_COLUMN:
            inside = True
            continue
        if not inside:
            continue
        if set(cells[0]) <= {"-", ":"} and cells[0]:
            continue
        match = NAME_CELL.match(cells[0])
        if match is None:
            found.append(
                f"unreadable-row: the first cell of a row under "
                f"'{FIRST_COLUMN}' is {cells[0]!r}, which is not one backticked "
                "name, so nothing can be held against the workflows"
            )
            continue
        rows.append(match.group(1))
    if not rows and not found:
        found.append(
            f"no-table: no table in {TABLE_DOCUMENT} carries a first column "
            f"headed '{FIRST_COLUMN}', so the rows this rule exists to hold "
            "against the tree were not found at all"
        )
    return rows, found


def _combinations(matrix: object) -> tuple[list[list[str]], str | None]:
    """The matrix combinations as lists of values, or the reason there are none.

    Refuses more than one key. The server joins several values into one
    parenthesised string and the order it uses is not derived from this tree, so
    a guess here produces a name that looks right and is not.
    """
    if not isinstance(matrix, dict):
        return [], "its matrix is not a mapping this file can read"
    keys = [key for key in matrix if key not in {"include", "exclude"}]
    if "include" in matrix or "exclude" in matrix:
        return [], (
            "its matrix carries include or exclude, which adds or removes combinations"
        )
    if len(keys) != 1:
        return [], (
            f"its matrix carries {len(keys)} keys, and the order the server "
            "joins their values in is not derivable from this tree"
        )
    values = matrix[keys[0]]
    if not isinstance(values, list) or not values:
        return [], f"the matrix key {keys[0]!r} is not a non-empty list of values"
    if not all(isinstance(value, str | int | float | bool) for value in values):
        return [], f"the matrix key {keys[0]!r} holds a value that is not a scalar"
    return [[str(value)] for value in values], None


def _substitute_with(values: dict[str, str]) -> Callable[[re.Match[str]], str]:
    """A substitution bound to one combination, so no closure reads a later one."""

    def replace(found: re.Match[str]) -> str:
        return values.get(found.group(1), found.group(0))

    return replace


def _job_names(job_id: str, job: object) -> tuple[list[str], list[str]]:
    """Every check name one job produces, or the reason it cannot be derived."""
    if not isinstance(job, dict):
        return [], [f"job {job_id!r} is not a mapping"]
    base = job.get("name")
    if base is None:
        base = job_id
    if not isinstance(base, str):
        return [], [f"job {job_id!r} carries a name that is not a string"]

    strategy = job.get("strategy")
    matrix = strategy.get("matrix") if isinstance(strategy, dict) else None
    if matrix is None:
        if EXPRESSION.search(base):
            return [], [
                f"job {job_id!r} names an expression and carries no matrix, so "
                "its check name depends on something outside this tree"
            ]
        return [base], []

    combinations, refusal = _combinations(matrix)
    if refusal is not None:
        return [], [f"job {job_id!r} cannot be expanded: {refusal}"]

    keys = [key for key in matrix if key not in {"include", "exclude"}]
    names: list[str] = []
    for values in combinations:
        substitution = dict(zip(keys, values, strict=True))
        if MATRIX_REFERENCE.search(base):
            name = MATRIX_REFERENCE.sub(
                _substitute_with(substitution),
                base,
            )
        else:
            name = f"{base} ({', '.join(values)})"
        if EXPRESSION.search(name):
            return [], [
                f"job {job_id!r} still names an expression once the matrix "
                "values are substituted"
            ]
        names.append(name)
    return names, []


def workflow_checks(
    workflows: Iterable[tuple[str, str]],
) -> tuple[dict[str, str], list[str]]:
    """Every check a pull request would show, mapped to the file producing it."""
    produced: dict[str, str] = {}
    found: list[str] = []
    for path, text in sorted(workflows):
        try:
            document = yaml.safe_load(text)
        except yaml.YAMLError as error:
            found.append(
                f"undecidable-workflow: {path} is not readable as YAML: {error}"
            )
            continue
        if not isinstance(document, dict):
            found.append(f"undecidable-workflow: {path} does not parse to a mapping")
            continue
        # `on` is a YAML boolean, so a workflow's trigger block arrives under
        # True rather than under the string somebody wrote.
        triggers = document.get(True, document.get("on"))
        names = triggers if isinstance(triggers, dict | list) else [triggers]
        if "pull_request" not in names:
            continue
        jobs = document.get("jobs")
        if not isinstance(jobs, dict):
            found.append(f"undecidable-workflow: {path} declares no jobs mapping")
            continue
        for job_id, job in jobs.items():
            derived, refusals = _job_names(str(job_id), job)
            found.extend(f"undecidable-workflow: {path}, {one}" for one in refusals)
            for name in derived:
                produced.setdefault(name, path)
    return produced, found


def failures(rows: Sequence[str], produced: dict[str, str]) -> list[str]:
    """Refusals for one table and one set of produced checks, as `kind: detail`.

    A pure function of what it is given, so the suite can hand it a tree that is
    one row or one job away from this one rather than editing the real files to
    find out what this rule would say.
    """
    named = set(rows)
    excepted = {name for name, _ in NOT_FROM_A_WORKFLOW}
    found: list[str] = []

    for name in rows:
        if name in produced or name in excepted:
            continue
        found.append(
            f"stale-row: `{name}` is a row in {TABLE_DOCUMENT} and no workflow "
            f"in {WORKFLOW_DIRECTORY} produces that check on a pull request, so "
            "the row describes something that does not run"
        )
    for name, path in sorted(produced.items()):
        if name in named:
            continue
        found.append(
            f"unnamed-check: `{name}` runs on a pull request, from {path}, and "
            f"no row in {TABLE_DOCUMENT} names it, so a contributor meeting it "
            "red has nothing to look it up in"
        )
    for name, reason in NOT_FROM_A_WORKFLOW:
        if name in produced:
            found.append(
                f"dangling-exception: `{name}` is declared as coming from "
                f"outside this tree ({reason}), and {produced[name]} now "
                "produces it, so the exemption has stopped being true"
            )
        if name not in named:
            found.append(
                f"unused-exception: `{name}` is declared as coming from outside "
                f"this tree, and no row in {TABLE_DOCUMENT} names it, so the "
                "exemption describes a row that went away"
            )
    return found


def report(rows: Sequence[str], produced: dict[str, str]) -> str:
    """What was compared, so a green run names its own coverage."""
    excepted = dict(NOT_FROM_A_WORKFLOW)
    lines = [
        f"{len(rows)} row(s) in {TABLE_DOCUMENT} against "
        f"{len(produced)} check(s) on a pull request:"
    ]
    for name in rows:
        where = produced.get(name)
        if where is None:
            lines.append(f"  `{name}` from outside this tree: {excepted[name]}")
        else:
            lines.append(f"  `{name}` from {where}")
    return "\n".join(lines)


def workflow_files(root: str) -> list[tuple[str, str]]:
    """Every workflow in the tree, with its text."""
    directory = os.path.join(root, *WORKFLOW_DIRECTORY.split("/"))
    found: list[tuple[str, str]] = []
    if not os.path.isdir(directory):
        return found
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith((".yml", ".yaml")):
            continue
        full = os.path.join(directory, filename)
        with open(full, encoding="utf-8") as handle:
            found.append((f"{WORKFLOW_DIRECTORY}/{filename}", handle.read()))
    return found


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refuse a table of checks that has drifted from the "
        "workflows in this tree, in both directions."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
        help="the repository root to read",
    )
    arguments = parser.parse_args(argv)

    document = os.path.join(arguments.root, TABLE_DOCUMENT)
    if not os.path.isfile(document):
        print(
            f"no {TABLE_DOCUMENT} below {arguments.root}, which is either the "
            "wrong root or a tree that lost the document holding the table",
            file=sys.stderr,
        )
        return 1
    workflows = workflow_files(arguments.root)
    if not workflows:
        print(
            f"no workflow below {arguments.root}/{WORKFLOW_DIRECTORY}, which is "
            "either the wrong root or a tree that lost its checks",
            file=sys.stderr,
        )
        return 1

    with open(document, encoding="utf-8") as handle:
        rows, found = table_names(handle.read())
    produced, refusals = workflow_checks(workflows)
    found.extend(refusals)
    found.extend(failures(rows, produced))

    for failure in found:
        print(failure, file=sys.stderr)
    if found:
        print(
            f"{len(found)} refusal(s) over {len(rows)} row(s) and "
            f"{len(workflows)} workflow(s)",
            file=sys.stderr,
        )
        return 1
    print(report(rows, produced))
    return 0


if __name__ == "__main__":
    sys.exit(main())
