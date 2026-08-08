"""Refuse a file under docs/decisions/ that is not a decision record.

Issue #1. Record 0001 fixes the shape: five sections with fixed headings, and a
number in the filename that is the number of the issue that decided the thing,
never reused. Until this ran, all of that was prose. A file with four of the
five sections landed as cleanly as a file with all of them, which is the state
where a directory of decision records quietly becomes a directory of notes.

Four arms, each refusing one thing and naming itself in the output so a red
result says which rule was broken before anybody opens the file.

  section-missing   one of the five headings is absent
  section-empty     a heading is there with nothing under it
  filename-shape    the name is not four digits, a hyphen and a slug
  number-reused     two files in the directory carry the same number

section-empty is separate from section-missing on purpose. Record 0001 rules out
a record with no reopening condition, and a heading with nothing under it
satisfies a check that only looks for headings while satisfying nothing a reader
wants. That is the near miss this arm exists for.

What this does not reach. Record 0001 also says a landed record is not
rewritten, and that a superseding record carries a sixth section naming the one
it replaces. Neither is checked here: the first is a fact about history rather
than about the file, and the second has no instance in the tree to prove itself
against. Both are stated in #1 rather than left to be discovered.

Standard library only, and no network. The input is the directory, read once.

    python tools/decision_records.py docs/decisions
"""

import argparse
import os
import re
import sys
from collections.abc import Sequence

# The five headings, exactly as record 0001 fixes them. This tuple is the
# authority the checker reads; docs/decisions/0000-template.md is the shape a
# writer copies, and the suite holds the two to each other.
REQUIRED_SECTIONS = (
    "## Question",
    "## Answer",
    "## Reasons",
    "## Ruled out",
    "## Reopened when",
)

# Four digits, a hyphen, a slug of lowercase words. The number is the issue
# number, which is why it is not required to be contiguous with its neighbours.
FILENAME = re.compile(r"^(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")

# A heading line and everything up to the next heading line or the end.
SECTION = re.compile(r"^(##[^\n]*)$", re.MULTILINE)


def section_bodies(text: str) -> dict[str, str]:
    """Map each heading in the file to the text under it.

    A heading repeated in one file keeps its first body, because a second
    heading of the same name is a defect this checker has no opinion about and
    silently preferring the last one would hide it.
    """
    bodies: dict[str, str] = {}
    marks = list(SECTION.finditer(text))
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
        heading = mark.group(1).rstrip()
        bodies.setdefault(heading, text[mark.end() : end].strip())
    return bodies


def file_failures(name: str, text: str) -> list[str]:
    """Refusals for one file, as `arm: detail` lines."""
    failures: list[str] = []

    if not FILENAME.match(name):
        failures.append(
            f"filename-shape: {name} is not four digits, a hyphen and a "
            "lowercase slug, so the record does not point at the issue that "
            "decided it"
        )

    bodies = section_bodies(text)
    for heading in REQUIRED_SECTIONS:
        if heading not in bodies:
            failures.append(
                f"section-missing: {name} has no '{heading}' section, so it is "
                "a note rather than a decision record"
            )
        elif not bodies[heading]:
            failures.append(
                f"section-empty: {name} has '{heading}' with nothing under it, "
                "which is the same absence with a heading in front of it"
            )
    return failures


def directory_failures(records: Sequence[tuple[str, str]]) -> list[str]:
    """Refusals that need more than one file to see.

    `records` is a sequence of (name, text) pairs.
    """
    failures: list[str] = []
    seen: dict[str, list[str]] = {}
    for name, _ in records:
        match = FILENAME.match(name)
        if not match:
            continue  # already refused by filename-shape
        number = match.group(1)
        seen.setdefault(number, []).append(name)
    for number, names in sorted(seen.items()):
        if len(names) > 1:
            failures.append(
                f"number-reused: {', '.join(sorted(names))} all carry the "
                f"number {number}, and a number is never reused"
            )
    return failures


def failures(records: Sequence[tuple[str, str]]) -> list[str]:
    """Every refusal for a directory, in a stable order."""
    found: list[str] = []
    for name, text in sorted(records):
        found.extend(file_failures(name, text))
    found.extend(directory_failures(records))
    return found


def read_directory(path: str) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for name in sorted(os.listdir(path)):
        full = os.path.join(path, name)
        if not os.path.isfile(full) or not name.endswith(".md"):
            continue
        with open(full, encoding="utf-8") as handle:
            records.append((name, handle.read()))
    return records


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refuse a file under docs/decisions/ that is not a record."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=os.path.join("docs", "decisions"),
        help="the directory of decision records to read",
    )
    arguments = parser.parse_args(argv)

    records = read_directory(arguments.directory)
    if not records:
        print(
            f"no markdown files under {arguments.directory}, which is either "
            "the wrong directory or a directory that lost its records",
            file=sys.stderr,
        )
        return 1

    found = failures(records)
    for failure in found:
        print(failure, file=sys.stderr)
    if found:
        print(
            f"{len(found)} refusal(s) over {len(records)} file(s) in "
            f"{arguments.directory}",
            file=sys.stderr,
        )
        return 1
    print(f"{len(records)} decision record(s) in {arguments.directory}, all in shape")
    return 0


if __name__ == "__main__":
    sys.exit(main())
