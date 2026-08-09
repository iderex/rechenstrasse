"""`CITATION.cff`, held against the tree rather than read once and trusted.

Issue #99. A citation file is the one artefact here whose reader is a machine
somebody else runs, in a bibliography this repository never sees, so a defect in
it surfaces as a wrong entry in a paper rather than as a red result. The two
failures worth a guard are the ones that look identical from inside the tree.

  a name that drifts
      The file names an author and `README.md` names a copyright holder. Two
      spellings of one person are two people to anything that cites
      automatically, and the second spelling is added by somebody who never saw
      the first. So the two are compared here rather than kept in step by hand.

  a field that resolves to nothing
      An identifier, a version or a date written in before the thing it names
      exists. That is the failure issue #99 warns about in its own words, and
      it cannot be caught by reading the file, because a key holding an empty
      string looks exactly like a key holding a value until something follows
      it.

What this does not do. It does not validate the file against the Citation File
Format schema, which would need a validator this tree does not carry and a
dependency it does not have. That the file is well formed YAML in the shape the
format asks for is checked here; that every rule of the format holds is not.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CITATION = ROOT / "CITATION.cff"
README = ROOT / "README.md"

# The line in README.md that says whose work this is. Held as a pattern rather
# than as a string, so the year moves without an edit here and the name does
# not.
COPYRIGHT = re.compile(r"^Copyright \(C\) \d{4} (?P<who>.+?)\.", re.M)

# The keys a release adds, and the key an author identifier adds. Each one is
# absent today because the thing it names does not exist, and each is what
# issue #99 fills in. This tuple is the debt: the day a release is cut, the
# case reading it goes red and is deleted in the same change that adds the key.
KEYS_A_RELEASE_BRINGS = ("version", "date-released", "doi", "identifiers")


def loaded() -> dict[str, Any]:
    """The file as data, or a failure that says the file is not a mapping.

    The shape check is here rather than only in the case below it, because the
    parser returns whatever the document happens to be. A citation file that
    parsed to a string would otherwise reach every case as something they read
    keys out of, and each would fail for a reason that is not the real one.
    """
    with CITATION.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if not isinstance(document, dict):
        raise AssertionError(
            f"{CITATION.name} parsed to {type(document).__name__} rather than to "
            "a mapping, so there is nothing in it to read"
        )
    return document


def test_the_citation_file_is_in_the_tree() -> None:
    assert CITATION.is_file(), f"no citation file at {CITATION.name}"


def test_it_parses() -> None:
    """The first half of the Done-when, and the half a typo takes out silently.

    A citation file that does not parse is not read by the tools that look for
    it. They skip it, and the repository shows no citation rather than a broken
    one, which is the failure that gets noticed last.
    """
    assert isinstance(loaded(), dict)


def test_it_declares_the_format_version_and_the_kind_of_thing_it_describes() -> None:
    document = loaded()
    assert document["cff-version"] == "1.2.0"
    assert document["type"] == "software"


def test_the_author_name_is_the_name_in_the_copyright_line() -> None:
    """The comparison this file exists for.

    Editing one spelling and not the other is the shape of this failure, and it
    is not caught by reading either file on its own.
    """
    match = COPYRIGHT.search(README.read_text(encoding="utf-8"))
    assert match is not None, "README.md carries no copyright line to hold against"
    authors = loaded()["authors"]
    assert len(authors) == 1
    named = f"{authors[0]['given-names']} {authors[0]['family-names']}"
    assert named == match.group("who")


def test_it_points_at_the_repository_it_is_in() -> None:
    assert loaded()["repository-code"] == "https://github.com/iderex/rechenstrasse"


def test_it_says_what_to_cite_and_sends_the_reader_where_that_is_written() -> None:
    """A citation file that only lists fields answers the wrong question.

    What a reader of a result needs is which version to cite, and this file's
    message is where they are told rather than left to guess.
    """
    message = loaded()["message"]
    assert "Citing this work" in message
    assert "README.md" in message


@pytest.mark.parametrize("key", KEYS_A_RELEASE_BRINGS)
def test_it_claims_nothing_a_release_has_not_produced_yet(key: str) -> None:
    """No release exists, so none of these keys has anything to hold.

    This is the assertion that goes red on the day a release is cut, and that is
    what it is for. It names the debt rather than leaving the absent keys to be
    noticed, and the change that mints an identifier deletes it here in the same
    breath as it adds the key there.
    """
    assert key not in loaded(), (
        f"{key!r} is in the citation file and issue #99 has not cut a release. "
        "If it has, this case is what the same change removes"
    )


def test_no_value_anywhere_in_it_resolves_to_nothing() -> None:
    """The general form of the failure the two cases above are instances of.

    An empty string, a null, or a placeholder somebody meant to come back to.
    Each of those is read by a bibliography tool as a value and printed as one.
    """
    placeholders = {"", "tbd", "todo", "none", "n/a", "xxx", "unknown"}
    empty: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}.{key}" if path else str(key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")
        elif node is None or (
            isinstance(node, str) and node.strip().lower() in placeholders
        ):
            empty.append(path)

    walk(loaded(), "")
    assert empty == []


def test_the_readme_says_how_to_cite_a_version() -> None:
    """The last clause of the Done-when that does not wait on an archive account.

    The file above is read by a machine. The section this asserts is what a
    person reads, and a citation file with nothing beside it leaves the question
    the issue actually asks, which version, unanswered.
    """
    readme = README.read_text(encoding="utf-8")
    assert "## Citing this work" in readme
    assert "CITATION.cff" in readme
