"""The third party notices, derived from the lock and the installed environment.

Issue #57. A notice listing what this tree installs from somewhere else, and
under which terms, is a document that goes stale the first time a dependency
moves, and it goes stale silently: nothing about the tree changes when the list
stops matching the lock. So it is generated rather than written, and the two
things it is generated from are the two that decide the answer.

`uv.lock` decides which distributions exist, which version of each, and which of
them are the runtime graph rather than the development group. That last
distinction is the part a hand-written notice gets wrong: a notice listing the
type checker beside the algebra library tells a reader that both travel with an
installed copy, and one of them does not.

The installed environment decides the terms. The lock carries no license field,
so a license written here would be a claim with nothing behind it. Every
distribution states its own terms in its metadata, and this reads them from
there, in the order the packaging metadata puts them in: a license expression
first, then a short license field, then the classifiers.

    python tools/third_party_notices.py                     # write to stdout
    python tools/third_party_notices.py --check THIRD-PARTY-NOTICES.md

The two modes are deliberately not the same strictness, and the reason is a
marker. A lock holds distributions that are installed on one platform and not on
another, `colorama` under `sys_platform == 'win32'` being the one this tree has
today. Writing the notice therefore requires an environment holding every
distribution in the lock and refuses by name if one is missing, so the file in
the tree is complete rather than a picture of one operating system. Checking it
requires every distribution in the lock to have a row with the version the lock
gives and the group the lock puts it in, and it verifies the terms column only
for the distributions this environment actually holds. What it could not verify
is printed rather than passed over, because a check that silently skips a row
reads exactly like one that verified it.

That is also the bound on what this produces. It reports the terms each
distribution declares about itself. It does not read a license file out of a
wheel, it does not verify that a declared expression matches the text shipped
beside it, and it says nothing about anything that is not in this lock.
"""

import argparse
import os
import re
import sys
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from importlib import metadata

# The project itself, which is in the lock as a package and is not a third party.
THIS_PROJECT = "rechenstrasse"

# The two groups a distribution can be in, and the sentence each one carries.
# Named here rather than at the call site, because the difference between them is
# the whole reason this file distinguishes anything.
RUNTIME = "runtime"
DEVELOPMENT = "development"
GROUPS: dict[str, str] = {
    RUNTIME: (
        "Installed with the package and present wherever it runs, so its terms "
        "travel with an installed copy."
    ),
    DEVELOPMENT: (
        "Installed only to build, check or test this tree, so it is not present "
        "in an installed copy and its terms do not travel with one."
    ),
}

# A `License` field longer than this is the license text rather than its name,
# which older packaging metadata allows and several distributions use. Read as a
# name only while it is short and on one line, and fall through to the
# classifiers otherwise.
LONGEST_LICENCE_NAME = 64

# The prefix a license classifier carries, and the separator inside it.
CLASSIFIER_PREFIX = "License :: "
CLASSIFIER_SEPARATOR = " :: "

# One row of the table, as it is written and as it is read back. The two are one
# expression and one format string so that a change to the shape moves both.
ROW = "| `{name}` | {version} | {terms} |"
ROW_PATTERN = re.compile(
    r"^\| `(?P<name>[^`]+)` \| (?P<version>[^|]*?) \| (?P<terms>.*?) \|$"
)


@dataclass(frozen=True)
class Row:
    """One distribution the lock holds, before its terms are read anywhere."""

    name: str
    version: str
    group: str


def lock(text: str) -> dict[str, object]:
    return tomllib.loads(text)


def _packages(document: dict[str, object]) -> dict[str, dict[str, object]]:
    listed = document.get("package")
    if not isinstance(listed, list):
        return {}
    return {
        entry["name"]: entry
        for entry in listed
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }


def _named(declared: object) -> list[str]:
    if not isinstance(declared, list):
        return []
    return [
        member["name"]
        for member in declared
        if isinstance(member, dict) and isinstance(member.get("name"), str)
    ]


def _closure(roots: Iterable[str], packages: dict[str, dict[str, object]]) -> set[str]:
    """Every distribution reachable from the roots, the roots included."""
    found: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in found or name not in packages:
            continue
        found.add(name)
        pending.extend(_named(packages[name].get("dependencies")))
    return found


def groups(document: dict[str, object]) -> dict[str, str]:
    """Which group each third party distribution in the lock is in.

    The runtime graph is what the project depends on and everything that reaches,
    which is the set an installed copy carries. Everything else in the lock is
    installed to work on this tree and never travels with it.
    """
    packages = _packages(document)
    project = packages.get(THIS_PROJECT, {})
    runtime = _closure(_named(project.get("dependencies")), packages)
    declared_dev = project.get("dev-dependencies")
    development: set[str] = set()
    if isinstance(declared_dev, dict):
        for members in declared_dev.values():
            development |= _closure(_named(members), packages)
    placed: dict[str, str] = {}
    for name in packages:
        if name == THIS_PROJECT:
            continue
        if name in runtime:
            placed[name] = RUNTIME
        elif name in development:
            placed[name] = DEVELOPMENT
    return placed


def rows(document: dict[str, object]) -> list[Row]:
    """Every third party distribution in the lock, sorted, from the lock alone.

    A pure function of the lock text, so what the notice has to hold is the same
    on every machine and only the terms column depends on an environment.
    """
    packages = _packages(document)
    placed = groups(document)
    return [
        Row(name, str(packages[name].get("version", "")), placed[name])
        for name in sorted(placed)
    ]


def terms_of(name: str) -> str | None:
    """What a distribution says about its own terms, or None where it says nothing.

    Read from the installed distribution rather than from the lock, which carries
    no such field.
    """
    declared = metadata.metadata(name)
    expression = declared.get("License-Expression")
    if expression:
        return str(expression).strip()
    written = declared.get("License")
    if written:
        single = str(written).strip()
        if "\n" not in single and len(single) <= LONGEST_LICENCE_NAME:
            return single
    classifiers = [
        str(line)[len(CLASSIFIER_PREFIX) :]
        for line in declared.get_all("Classifier") or []
        if str(line).startswith(CLASSIFIER_PREFIX)
    ]
    if classifiers:
        return ", ".join(
            sorted(line.rsplit(CLASSIFIER_SEPARATOR, 1)[-1] for line in classifiers)
        )
    return None


def installed(names: Iterable[str]) -> dict[str, str]:
    """The terms this environment can read, for the names it holds.

    A name this environment does not hold is absent from the result rather than
    present with an empty value, because "not installed here" and "declares
    nothing" are different states and the second is a defect.
    """
    found: dict[str, str] = {}
    for name in names:
        try:
            declared = terms_of(name)
        except metadata.PackageNotFoundError:
            continue
        if declared is None:
            raise SystemExit(
                f"{name} is installed here and declares no license expression, no "
                "license field and no license classifier, so its terms cannot be "
                "read. A notice that guessed would be worse than none"
            )
        found[name] = declared
    return found


def render(listed: Sequence[Row], terms: Mapping[str, str]) -> str:
    """The notice itself, which is what somebody redistributing this reads."""
    lines = [
        "# Third party notices",
        "",
        "Generated from `uv.lock` and from the metadata each distribution states",
        "about itself, by the command README.md carries. Not written by hand, and",
        "`tools/test_third_party_notices.py` proves the rule that refuses a copy",
        "which has drifted from the lock.",
        "",
        "The terms below are what each distribution declares about itself. Nothing",
        "here reads a license file out of a wheel or checks that a declared",
        "expression matches the text shipped beside it.",
        "",
    ]
    for group, because in GROUPS.items():
        lines.extend([f"## The {group} group", "", because, ""])
        inside = [row for row in listed if row.group == group]
        if not inside:
            lines.extend(["Nothing in this lock is in this group.", ""])
            continue
        lines.append("| Distribution | Version | Terms it declares |")
        lines.append("| --- | --- | --- |")
        for row in inside:
            lines.append(
                ROW.format(name=row.name, version=row.version, terms=terms[row.name])
            )
        lines.append("")
    return "\n".join(lines)


def written_rows(text: str) -> dict[str, tuple[str, str]]:
    """The table rows a notice already carries, by name, as version and terms."""
    found: dict[str, tuple[str, str]] = {}
    for line in text.splitlines():
        match = ROW_PATTERN.match(line)
        if match is None or match.group("name") == "Distribution":
            continue
        found[match.group("name")] = (match.group("version"), match.group("terms"))
    return found


def differences(
    listed: Sequence[Row], terms: Mapping[str, str], on_disk: str
) -> list[str]:
    """Why a notice in the tree is not what the lock and this environment say.

    A pure function of its three arguments, so the suite can hand it a notice one
    line away from the real one rather than writing a wrong file into the tree to
    find out what this would say about it.
    """
    carried = written_rows(on_disk)
    found: list[str] = []
    for row in listed:
        if row.name not in carried:
            found.append(
                f"missing: the lock holds {row.name} and the notice has no row for "
                "it, so a reader is not told about something this tree installs"
            )
            continue
        version, declared = carried[row.name]
        if version != row.version:
            found.append(
                f"version: the notice says {row.name} {version} and the lock says "
                f"{row.version}"
            )
        if row.name in terms and declared != terms[row.name]:
            found.append(
                f"terms: the notice says {row.name} declares {declared!r} and this "
                f"environment reads {terms[row.name]!r}"
            )
    for name in sorted(set(carried) - {row.name for row in listed}):
        found.append(
            f"stale: the notice has a row for {name}, which is not in the lock, so "
            "it describes something this tree does not install"
        )
    # The grouping, read back out of the rendered document rather than trusted.
    # A distribution that moved between the two groups is the change this notice
    # exists to report and the one a row comparison alone would not see.
    for row in listed:
        heading = f"## The {row.group} group"
        section = on_disk.split(heading)
        if len(section) != 2 or f"`{row.name}`" not in section[1].split("\n## ")[0]:
            found.append(
                f"group: the lock puts {row.name} in the {row.group} group and the "
                "notice does not carry it under that heading"
            )
    return found


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write the third party notices, or refuse a copy that has "
        "drifted from the lock and the installed environment."
    )
    here = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument(
        "--lock",
        default=os.path.join(here, "..", "uv.lock"),
        help="the lock file to read",
    )
    parser.add_argument(
        "--check",
        default=None,
        help="a notice file to hold against the lock rather than writing one",
    )
    arguments = parser.parse_args(argv)

    with open(arguments.lock, encoding="utf-8") as handle:
        document = lock(handle.read())
    listed = rows(document)
    terms = installed(row.name for row in listed)
    absent = [row.name for row in listed if row.name not in terms]

    if arguments.check is None:
        if absent:
            print(
                "this environment does not hold "
                + ", ".join(sorted(absent))
                + ", which the lock does, so a notice written here would be a "
                "picture of one platform. Write it where every distribution in "
                "the lock is installed",
                file=sys.stderr,
            )
            return 1
        sys.stdout.write(render(listed, terms))
        return 0

    with open(arguments.check, encoding="utf-8") as handle:
        on_disk = handle.read()
    found = differences(listed, terms, on_disk)
    for reason in found:
        print(reason, file=sys.stderr)
    if found:
        print(
            f"{len(found)} refusal(s) over {len(listed)} distribution(s) in the "
            "lock. Regenerate the notice rather than editing it",
            file=sys.stderr,
        )
        return 1
    print(
        f"{arguments.check} carries all {len(listed)} distribution(s) the lock "
        f"holds, with the version the lock gives and the group it puts each in. "
        f"The terms column was verified for {len(terms)} of them."
    )
    if absent:
        print(
            "not verified here, because this environment does not hold them: "
            + ", ".join(sorted(absent))
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
