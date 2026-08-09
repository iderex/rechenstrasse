"""The theory documents in `theories/`, read against the schema and the gate.

Issue #29. The documents are inputs, and what is asserted here is the whole of
what makes them inputs worth having: each is readable as the plain data record
0004 fixes, each is in the shape of the schema of #24, each is placed as covered
by the gate of #26, and each carries the reference it came from and the
convention it is written in.

The legs are written over the directory rather than over four names, so a fifth
document arriving is judged by all of them without an edit here. The four record
0011 names are asserted by identifier on top of that, because "every document in
the directory passes" is also true of a directory holding one document, and the
issue asks for four.

Two legs are the near miss, and they are the reason the covered verdicts above
are not vacuous. A covered document one edit away from a refused family is
refused, and a covered document one edit away from the conventions record 0008
fixes is unplaceable rather than covered. Without them a gate that returned
`covered` for everything would pass this file.

The documents carry no expected value and nothing here compares one. That is the
separation issue #29 asks for and record 0011 argues for from the other side, and
the parity check of #42 is where a value is read.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from rechenstrasse.admissibility import gate
from rechenstrasse.document import schema

ROOT = Path(__file__).resolve().parents[2]
THEORIES = ROOT / "theories"

# The four entries record 0011 names, by the identifier each document carries.
# A list in a test rather than in a document, and it fails closed: an entry that
# leaves the tree reds this file instead of leaving the corpus quietly smaller.
RECORD_0011_ENTRIES = (
    "general-relativity-with-a-cosmological-constant",
    "brans-dicke",
    "metric-f-of-r-as-a-scalar-tensor-theory",
    "covered-horndeski-sector",
)


def documents() -> list[tuple[str, dict[str, Any]]]:
    """Every theory document in the tree, by file name stem, sorted."""
    found: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(THEORIES.glob("*.json")):
        loaded = json.loads(path.read_text(encoding="utf-8"))
        found.append((path.stem, loaded))
    return found


def named(stem: str) -> dict[str, Any]:
    return dict(documents())[stem]


ALL = documents()
STEMS = [stem for stem, _ in ALL]


def test_the_directory_holds_documents() -> None:
    # An empty directory passes every leg below by having nothing to fail, which
    # is the shape a moved directory or a wrong root arrives in.
    assert ALL, f"no theory document below {THEORIES}, which is not a pass"


@pytest.mark.parametrize("stem", STEMS)
def test_a_document_is_in_the_shape_of_the_schema(stem: str) -> None:
    refusals = schema.refusals(named(stem))
    assert list(refusals) == [], [
        f"{refusal.rule} at {refusal.where}: {refusal.detail}" for refusal in refusals
    ]


@pytest.mark.parametrize("stem", STEMS)
def test_a_document_is_placed_as_covered_and_reaches_the_next_stage(stem: str) -> None:
    verdict = gate.classify(named(stem))
    assert verdict.state == gate.COVERED, [reason.detail for reason in verdict.reasons]
    assert verdict.reaches_the_next_stage()
    # Record 0003's own sentence, which the gate holds to: a covered verdict
    # states why rather than reporting the absence of an objection.
    assert verdict.reasons != ()


@pytest.mark.parametrize("stem", STEMS)
def test_a_document_carries_a_citation(stem: str) -> None:
    citation = named(stem)["metadata"]["citation"]
    assert citation.strip() != ""


@pytest.mark.parametrize("stem", STEMS)
def test_a_document_carries_the_convention_it_is_written_in(stem: str) -> None:
    # The signature record 0008 fixes, written in the document rather than
    # assumed by whatever reads it. The gate refuses any other one, and the near
    # miss below is what proves that.
    assert named(stem)["manifold"]["signature"] == gate.COVERED_SIGNATURE


@pytest.mark.parametrize("stem", STEMS)
def test_the_file_name_is_the_identifier_a_result_will_cite(stem: str) -> None:
    # A run record and a parity row refer to the identifier. If the two can drift,
    # a document can be renamed without the thing citing it noticing.
    assert named(stem)["metadata"]["identifier"] == stem


def test_the_four_entries_of_record_0011_are_in_the_tree() -> None:
    missing = [entry for entry in RECORD_0011_ENTRIES if entry not in STEMS]
    assert missing == [], f"record 0011 names these and the tree has none: {missing}"


@pytest.mark.parametrize("stem", STEMS)
def test_one_edit_puts_a_document_in_a_refused_family(stem: str) -> None:
    """The near miss. These documents are covered, and only just.

    One term head away from the covered Horndeski sector is the sector record
    0003 refuses for its derivative couplings, and that edit is the one an author
    widening a document actually makes.
    """
    document = named(stem)
    document["lagrangian"]["terms"].append(
        {"head": "horndeski_g5", "coefficient": "G5_of_phi_and_X"}
    )
    verdict = gate.classify(document)
    assert verdict.state == gate.REFUSED
    assert "derivative-coupling" in [reason.about for reason in verdict.reasons]


@pytest.mark.parametrize("stem", STEMS)
def test_one_edit_puts_a_document_outside_the_conventions(stem: str) -> None:
    """The second near miss, and the one the citation half rests on.

    A document written in the other signature is not refused by name, because no
    family record 0003 lists covers it. It is unplaceable, which is what the gate
    reports for something it can place in neither set.
    """
    document = named(stem)
    document["manifold"]["signature"] = "(+, -, -, -)"
    verdict = gate.classify(document)
    assert verdict.state == gate.UNPLACEABLE
    assert "signature" in [reason.about for reason in verdict.reasons]


def test_a_document_with_a_scalar_carries_what_the_gate_did_not_decide() -> None:
    """A covered verdict over a scalar theory is the narrower kind.

    Record 0003 refuses a scalar whose mass puts the range of the extra force
    inside the regime being asked about, and the gate does not decide that. Three
    of the four documents declare a scalar, so three of them carry the entry, and
    a covered verdict that dropped it would read as a wider statement than it is.
    """
    with_scalar = [
        stem
        for stem, document in ALL
        if any(member["role"] == "scalar" for member in document["fields"])
    ]
    assert with_scalar, "no document here declares a scalar field"
    for stem in with_scalar:
        verdict = gate.classify(named(stem))
        assert gate.SCALAR_FORCE_RANGE in [
            reason.about for reason in verdict.not_evaluated
        ]
