"""The coverage bar, pinned on the surface that decides an answer.

Issue #49. A number over everything says very little: a tree can carry a high
one while the code that decides whether an operator gets an answer, and which
answer, is the part nobody exercised. So the bar is pinned on that surface by
name, and the number over the whole tree is printed beside it and gates nothing.

The surface is the list below. Record 0003's gate decides whether this pipeline
will answer at all, and the post-Newtonian bookkeeping decides which terms
survive a truncation, which is the same kind of decision one stage further in.
The variation stage and the parity comparison belong here too and are not in the
tree yet, so the list is data with a reason per entry rather than a glob, and it
grows in the change that adds the stage.

It fails closed in four ways, and three of them are the ones this issue exists
against:

  below
      The surface is measured under the bar. The ordinary failure, and the only
      one anybody expects.

  unreadable
      The report is not a coverage report this can read. A check that treats an
      unreadable report as nothing to complain about is a check that passes
      whenever the measurement step quietly broke.

  empty
      A report this can read that matched no line on the surface. That is what a
      renamed module, a wrong root or a measurement that ran over nothing looks
      like, and it is the state that most resembles a clean pass.

  dangling
      An entry naming a file the report does not hold. The surface moved and the
      list is now describing something that is not there, so the bar is being
      taken over less than it says.

What this does not do. It reads a report and never produces one, so whether the
measurement it reads covered the run it claims to is decided by the step that
made it. And a percentage over a surface says nothing about which line went
uncovered, which is what `coverage report` beside it is for.

    python tools/coverage_bar.py --report .coverage.json --bar 90
"""

import argparse
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass

# The bar, and the measurement it was chosen from. Both are in the pull request
# that landed this and in issue #49, so moving it is an argument rather than an
# edit to a number nobody can source.
DEFAULT_BAR = 90.0


@dataclass(frozen=True)
class Surface:
    """One file that decides an answer, and why it is on this list."""

    # The tail of the path, with forward slashes, so the entry reads the same on
    # a report written on any operating system.
    path: str
    because: str


SURFACE: tuple[Surface, ...] = (
    Surface(
        path="src/rechenstrasse/admissibility/gate.py",
        because=(
            "it decides whether this pipeline answers at all, and an arm of it "
            "that nothing exercises is a document reaching the algebra that "
            "record 0003 says must not"
        ),
    ),
    Surface(
        path="src/rechenstrasse/document/reader.py",
        because=(
            "it decides whether a document becomes the action the later stages "
            "derive from, and an arm of it that nothing exercises is a theory "
            "reaching the algebra with a mention resolved to the wrong "
            "declaration or to none"
        ),
    ),
    Surface(
        path="src/rechenstrasse/variation/metric.py",
        because=(
            "it is the first stage that computes rather than reads, and an arm "
            "of it that nothing exercises is a term of the action that reaches "
            "no field equation while the equation still looks like one"
        ),
    ),
    Surface(
        path="src/rechenstrasse/ppn/bookkeeping.py",
        because=(
            "it decides which terms survive a truncation and at what order, and "
            "an uncounted derivative there is a term that crossed the cut and "
            "looks exactly like one that belonged"
        ),
    ),
)


@dataclass(frozen=True)
class Measurement:
    """What was measured over the surface, in points rather than percentages."""

    covered: int
    total: int
    per_file: tuple[tuple[str, float], ...]

    def percentage(self) -> float:
        return 100.0 * self.covered / self.total


def load(text: str) -> dict[str, object] | None:
    """The report, or None where these bytes are not one this can read."""
    try:
        report = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(report, dict) or not isinstance(report.get("files"), dict):
        return None
    return report


def measure(report: dict[str, object], surface: Sequence[Surface]) -> Measurement:
    """Covered points over total points on the surface, and the per-file numbers.

    Branches count beside statements, because a stage that refuses on one arm
    and returns on the other is the shape this pipeline is made of and a
    statement count cannot tell those two apart.
    """
    files = report["files"]
    assert isinstance(files, dict)
    covered = 0
    total = 0
    per_file: list[tuple[str, float]] = []
    for entry in surface:
        for name, held in sorted(files.items()):
            if not name.replace("\\", "/").endswith(entry.path):
                continue
            summary = held["summary"]
            covered += summary["covered_lines"] + summary["covered_branches"]
            total += summary["num_statements"] + summary["num_branches"]
            per_file.append((entry.path, float(summary["percent_covered"])))
    return Measurement(covered, total, tuple(per_file))


def missing(report: dict[str, object], surface: Sequence[Surface]) -> list[str]:
    """Surface entries the report holds no file for."""
    files = report["files"]
    assert isinstance(files, dict)
    present = {name.replace("\\", "/") for name in files}
    return [
        entry.path
        for entry in surface
        if not any(name.endswith(entry.path) for name in present)
    ]


def failures(text: str, bar: float, surface: Sequence[Surface] = SURFACE) -> list[str]:
    """Refusals for one report, as `kind: detail` lines.

    A pure function of the bytes and the bar, so the suite hands it a report one
    number away from a passing one rather than having to run a measurement to
    find out what this would say about it.
    """
    report = load(text)
    if report is None:
        return [
            "unreadable: these bytes are not a coverage report with a file table "
            "in them, and a bar that reads an unreadable report as nothing to "
            "complain about passes whenever the measurement broke"
        ]
    found = [
        f"dangling: the surface names {path}, which this report holds no file "
        "for, so the bar is taken over less of the tree than the list says"
        for path in missing(report, surface)
    ]
    taken = measure(report, surface)
    if taken.total == 0:
        found.append(
            "empty: the report matched no statement or branch on the surface, "
            "which is what a wrong root or a measurement over nothing looks "
            "like, and it is the state that most resembles a clean pass"
        )
        return found
    if taken.percentage() < bar:
        found.append(
            f"below: the surface is {taken.percentage():.2f} percent covered, "
            f"{taken.covered} of {taken.total} points, and the bar is {bar:.2f}"
        )
    return found


def report_lines(taken: Measurement, bar: float) -> list[str]:
    lines = [
        f"the surface that decides an answer is {taken.percentage():.2f} percent "
        f"covered, {taken.covered} of {taken.total} statements and branches, "
        f"against a bar of {bar:.2f}:"
    ]
    for path, percentage in taken.per_file:
        lines.append(f"  {path}  {percentage:.2f}")
    for entry in SURFACE:
        lines.append(f"  {entry.path}, because {entry.because}")
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refuse a coverage report that puts the surface deciding an "
        "answer under the bar, that cannot be read, or that measured nothing."
    )
    here = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument(
        "--report",
        default=os.path.join(here, "..", ".coverage.json"),
        help="the coverage report to read, as written by `coverage json`",
    )
    parser.add_argument(
        "--bar",
        type=float,
        default=DEFAULT_BAR,
        help="the percentage the surface may not fall under",
    )
    arguments = parser.parse_args(argv)

    if not os.path.isfile(arguments.report):
        print(
            f"no coverage report at {arguments.report}. A missing report is the "
            "same failure as an unreadable one and is refused for the same "
            "reason",
            file=sys.stderr,
        )
        return 1
    with open(arguments.report, encoding="utf-8") as handle:
        text = handle.read()

    found = failures(text, arguments.bar)
    for reason in found:
        print(reason, file=sys.stderr)
    if found:
        print(f"{len(found)} refusal(s) against the bar", file=sys.stderr)
        return 1

    report = load(text)
    assert report is not None
    for line in report_lines(measure(report, SURFACE), arguments.bar):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
