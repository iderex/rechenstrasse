"""The statement about what stays on the host, held in the two places it lives.

Issue #54 asks for the statement in `README.md` and in `docs/privacy.md`. Two
copies of a promise maintained by hand drift, and a promise that says two
different things in two places is worse than one that is written once, because a
reader who found the weaker copy has been told less than the project means.

So the two are held against each other by a command rather than by memory.
`docs/privacy.md` is the one the statement is read out of, under the heading it
carries, and `README.md` has to contain that text byte for byte. Nothing here
judges whether the statement is true; that is what the page around it is for and
what the guards it names are for.

The other leg is the pointer the issue asks for. `NOTICE.md` is the file a
reader is sent to for the intended-use notice, and it has to name the page.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PRIVACY = ROOT / "docs" / "privacy.md"
README = ROOT / "README.md"
NOTICE = ROOT / "NOTICE.md"

# The heading the statement sits under, and the pattern that ends it. A section
# is read rather than a line count, so a paragraph added to the statement is
# carried by this leg without an edit here.
HEADING = "## The statement\n"


def statement_of(text: str) -> str:
    """The section under the heading above, with nothing around it."""
    start = text.index(HEADING) + len(HEADING)
    rest = text[start:]
    ends = re.search(r"^## ", rest, flags=re.MULTILINE)
    return rest[: ends.start()].strip() if ends else rest.strip()


def test_the_statement_is_the_same_text_in_both_documents() -> None:
    """One statement, two documents, and a command that says so.

    The extraction is asserted first, because a heading renamed in
    `docs/privacy.md` would otherwise make this leg pass on an empty string
    against a `README.md` that contains one.
    """
    statement = statement_of(PRIVACY.read_text(encoding="utf-8"))
    assert "runs offline" in statement
    assert len(statement.splitlines()) > 5
    assert statement in README.read_text(encoding="utf-8")


def test_the_statement_says_what_installing_does_rather_than_only_computing() -> None:
    """The half the issue asks for that a shorter promise would leave out.

    A promise that overreaches is worth less than a narrow one that holds. The
    dependencies an operator installs come from wherever their package tooling
    is configured to fetch them, and that is their own network activity rather
    than this pipeline's, so the statement has to separate the two rather than
    say the whole thing is offline and leave a reader to find out.
    """
    statement = statement_of(PRIVACY.read_text(encoding="utf-8"))
    assert "Installing the pipeline is a different thing" in statement
    assert "does not cover it" in statement


def test_the_notice_points_at_the_page() -> None:
    """The notice sends a reader on rather than restating the statement."""
    notice = NOTICE.read_text(encoding="utf-8")
    assert "docs/privacy.md" in notice
    assert statement_of(PRIVACY.read_text(encoding="utf-8")) not in notice


@pytest.mark.parametrize(
    "planted",
    [
        # One word changed in the copy that is not the source, which is the
        # drift this leg exists against.
        ("it collects no usage data", "it collects little usage data"),
        # The half about installing dropped from the copy, which is the
        # overreaching promise the issue refuses.
        ("Installing the pipeline is a different thing", "Installing is fine"),
    ],
)
def test_a_copy_that_drifted_is_caught(planted: tuple[str, str]) -> None:
    """The proof the leg above bites, on the text rather than on the tree.

    The mistake is planted in a copy of what `README.md` holds rather than in
    the file, so the tree is not edited to prove a guard about the tree. Both
    plantings are one phrase somebody would actually write while tightening a
    sentence in one document and not the other.
    """
    before, after = planted
    statement = statement_of(PRIVACY.read_text(encoding="utf-8"))
    assert before in statement
    drifted = README.read_text(encoding="utf-8").replace(before, after)
    assert statement not in drifted
