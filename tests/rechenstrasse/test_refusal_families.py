"""One fixture and one near miss for every refusal the admissibility gate holds.

Issue #27, over the families record 0003 names. The gate of #26 already had
tests, and what they proved about a family was weaker than it read. The cases
were parametrised over the gate's own tables, so a refusal and the only test
naming it were the same line of source, and deleting the refusal deleted its
proof rather than reddening it. Measured before this file existed, by removing
one entry from `ROLE_FAMILIES` and running the suite:

    .venv/Scripts/python.exe -m pytest -q tests/
    229 passed, 2 deselected, 1 xfailed        # the tree as it stands
    228 passed, 2 deselected, 1 xfailed        # with the aether refusal removed

Nothing went red. One case was collected that had been collected before, and a
count nobody was watching moved by one.

So the pairs below are written out by hand. Each names the refusal it is about
in this file rather than reading it out of the gate, which is the whole point:
the fixture stays after the refusal it trips has gone, and the test that names
the family goes red.

Each refused fixture is paired with a near miss, a document one edit away from
it that is covered and has to pass. The edit is named in the pair, because a
refusal firing on everything nearby draws no boundary and the near miss is the
only thing that says otherwise.

## What this file does not cover

Record 0003 refuses six things and the pairs below reach five of them. The sixth
is a scalar whose mass puts the range of the extra force inside the regime the
operator is asking about. That is a property of the input rather than of a
theory, this gate does not decide it, and it says so in the `not_evaluated` list
of every covered verdict over a document with a scalar. A fixture that trips it
cannot be written while nothing refuses it. Issue #41 is where that refusal is
built, and the pair belongs with it rather than here.

The input the gate can place in neither set is refused as well, and it is not
one of the six families. Its fixtures are in `test_admissibility.py`, which
asserts the identity of each unplaceable reason and pairs the two conventions
cases with a near miss. Nothing here restates them.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from rechenstrasse.admissibility import gate


def covered() -> dict[str, Any]:
    """General relativity with a cosmological constant, inside the covered class.

    The base every pair below edits, and it carries no scalar field, so a pair
    that adds one is adding the only one and stays inside the covered class for
    that reason rather than by accident.
    """
    return {
        "schema_version": 1,
        "metadata": {
            "identifier": "the-base-of-a-refusal-pair",
            "name": "General relativity with a cosmological constant",
            "citation": "a fixture, and not a claim about any published source",
        },
        "manifold": {"dimension": 4, "signature": "(-, +, +, +)"},
        "fields": [{"symbol": "g", "role": "metric", "symmetries": ["symmetric"]}],
        "lagrangian": {
            "terms": [
                {"head": "ricci_scalar", "coefficient": "one_over_two_kappa"},
                {"head": "cosmological_constant", "coefficient": "Lambda"},
            ]
        },
        "matter": {"coupling": "minimal", "frame": "jordan"},
        "parameters": [
            {
                "symbol": "Lambda",
                "minimum": None,
                "maximum": None,
                "claimed_by": "a fixture",
            }
        ],
        "regime": {"name": "solar system", "length_scale": "astronomical unit"},
    }


def with_term(head: str) -> dict[str, Any]:
    """The base with one more term, which is the edit a widening author makes."""
    document = covered()
    document["lagrangian"]["terms"].append({"head": head, "coefficient": "c"})
    return document


def with_field(role: str, symmetries: tuple[str, ...] = ()) -> dict[str, Any]:
    """The base with one more field, which is the edit a widening author makes."""
    document = covered()
    document["fields"].append(
        {"symbol": "X", "role": role, "symmetries": list(symmetries)}
    )
    return document


@dataclass(frozen=True)
class Pair:
    """One refused document, the family it has to be refused by, and its near miss.

    `site` says which refusal in the gate this pair is about, in the gate's own
    terms: a term head, a field role, or an arm that is neither. It is what the
    coverage assertion at the foot of this file reads, and it is a string here
    rather than a lookup into the gate, so that a refusal leaving the gate leaves
    this pair behind rather than taking it along.
    """

    name: str
    site: tuple[str, str]
    family: str
    refused: dict[str, Any]
    near_miss: dict[str, Any]
    # What separates the two documents, in one phrase. A pair whose edit cannot
    # be said in one phrase is not a near miss, it is a second fixture.
    edit: str


PAIRS: tuple[Pair, ...] = (
    Pair(
        name="G4 with kinetic dependence",
        site=("head", "horndeski_g4_kinetic"),
        family="derivative-coupling",
        refused=with_term("horndeski_g4_kinetic"),
        near_miss=with_term("horndeski_g4"),
        edit=(
            "the same G4 term with the dependence on the kinetic scalar dropped, "
            "which is G4 a function of the field alone and is what record 0003 "
            "admits"
        ),
    ),
    Pair(
        name="any G5",
        site=("head", "horndeski_g5"),
        family="derivative-coupling",
        refused=with_term("horndeski_g5"),
        near_miss=with_term("horndeski_g3"),
        edit=(
            "one step down the Horndeski ladder to G3, which is free in the "
            "covered sector"
        ),
    ),
    Pair(
        name="the torsion scalar of a teleparallel theory",
        site=("head", "torsion_scalar"),
        family="torsional-geometry",
        refused=with_term("torsion_scalar"),
        near_miss=with_term("ricci_scalar"),
        edit=(
            "the curvature scalar in place of the torsion scalar, which is the "
            "same term written for the Levi-Civita connection every variational "
            "step here assumes"
        ),
    ),
    Pair(
        name="the Gauss-Bonnet term",
        site=("head", "gauss_bonnet"),
        family="quadratic-curvature",
        refused=with_term("gauss_bonnet"),
        near_miss=with_term("ricci_scalar"),
        edit="a curvature term that is linear rather than quadratic",
    ),
    Pair(
        name="the Ricci tensor squared",
        site=("head", "ricci_squared"),
        family="quadratic-curvature",
        refused=with_term("ricci_squared"),
        near_miss=with_term("ricci_scalar"),
        edit="a curvature term that is linear rather than quadratic",
    ),
    Pair(
        name="the Riemann tensor squared",
        site=("head", "riemann_squared"),
        family="quadratic-curvature",
        refused=with_term("riemann_squared"),
        near_miss=with_term("ricci_scalar"),
        edit="a curvature term that is linear rather than quadratic",
    ),
    Pair(
        name="the vector of a vector-tensor theory",
        site=("role", "vector"),
        family="preferred-frame",
        refused=with_field("vector"),
        near_miss=with_field("scalar"),
        edit=(
            "the extra field carrying no direction, which is the one additional "
            "field the covered class takes"
        ),
    ),
    Pair(
        name="the aether field",
        site=("role", "aether"),
        family="preferred-frame",
        refused=with_field("aether"),
        near_miss=with_field("scalar"),
        edit=(
            "the extra field carrying no direction, which is the one additional "
            "field the covered class takes"
        ),
    ),
    Pair(
        name="a tetrad as the variable",
        site=("role", "tetrad"),
        family="torsional-geometry",
        refused=with_field("tetrad"),
        near_miss=with_field("scalar"),
        edit=(
            "the extra field carrying no frame, so the geometry stays the one "
            "the metric already in the document describes"
        ),
    ),
    Pair(
        name="a torsion field",
        site=("role", "torsion"),
        family="torsional-geometry",
        refused=with_field("torsion"),
        near_miss=with_field("scalar"),
        edit=(
            "the extra field carrying no torsion, so the connection stays Levi-Civita"
        ),
    ),
    Pair(
        name="a second metric declared as one",
        site=("role", "second_metric"),
        family="second-metric",
        refused=with_field("second_metric"),
        near_miss=with_field("scalar"),
        edit="the second field being a scalar rather than a second geometry",
    ),
    Pair(
        name="a second metric declared as a metric",
        site=("arm", "more than one field with the role metric"),
        family="second-metric",
        refused=with_field("metric", ("symmetric",)),
        near_miss=with_field("scalar"),
        edit=(
            "the role on the second field, and it is the edit that matters most "
            "here: a bimetric document is not written with a role called "
            "`second_metric`, it is written as two fields that both say `metric`, "
            "and a gate reading roles one at a time takes each of them for the "
            "one the covered class carries"
        ),
    ),
)

IDS = [pair.name for pair in PAIRS]


@pytest.mark.parametrize("pair", PAIRS, ids=IDS)
def test_the_fixture_is_refused_by_the_family_it_names(pair: Pair) -> None:
    """The proof that one refusal bites, and the only test in this file that reds.

    Three assertions rather than one, because "something failed" is what this
    issue exists against. The state, the identity of the family, and the reason
    being record 0003's own sentence rather than a paraphrase are one statement
    about one refusal, and splitting them across three tests would turn one
    deleted refusal into three red results that all say the same thing.
    """
    verdict = gate.classify(pair.refused)
    assert verdict.state == gate.REFUSED, [reason.detail for reason in verdict.reasons]
    assert sorted({reason.about for reason in verdict.reasons}) == [pair.family]
    assert gate.FAMILIES[pair.family] in " ".join(
        reason.detail for reason in verdict.reasons
    )
    assert not verdict.reaches_the_next_stage()


@pytest.mark.parametrize("pair", PAIRS, ids=IDS)
def test_the_near_miss_is_covered_and_reaches_the_next_stage(pair: Pair) -> None:
    """The other half, and it is the half that says the boundary is a boundary.

    This one does not move when a refusal is deleted, which is deliberate. A
    near miss is covered whether or not the refusal beside it exists, so a
    deleted refusal reds the test above and this one stays green, and the count
    of red results is the count of refusals that went missing.
    """
    verdict = gate.classify(pair.near_miss)
    assert verdict.state == gate.COVERED, [reason.detail for reason in verdict.reasons]
    assert verdict.reaches_the_next_stage()


@pytest.mark.parametrize("pair", PAIRS, ids=IDS)
def test_the_two_documents_of_a_pair_are_not_the_same_document(pair: Pair) -> None:
    """A pair whose halves are equal proves nothing and reads as though it did.

    The cheapest way for this file to go quietly worthless is an edit that makes
    a near miss identical to the document it is a near miss for, at which point
    both tests above pass for a reason that has nothing to do with the gate.
    """
    assert pair.refused != pair.near_miss, pair.edit


def test_every_refusal_the_gate_holds_has_a_pair_here() -> None:
    """The direction that catches a refusal arriving without a fixture.

    It reads the gate's tables, so it moves when they do, and it moves in one
    direction only: a refusal added to the gate with no pair here is red, and a
    refusal removed from the gate is not this test's business. That is the split
    the issue asks for. The removal is caught by the pair's own test above, and a
    second assertion over the same removal would only say it twice.
    """
    held = (
        {("head", head) for head in gate.HEAD_FAMILIES}
        | {("role", role) for role in gate.ROLE_FAMILIES}
        | {("arm", "more than one field with the role metric")}
    )
    assert sorted(held - {pair.site for pair in PAIRS}) == []


def test_every_family_record_0003_refuses_by_name_has_a_pair_here() -> None:
    """The same direction over the families rather than over the sites.

    A family every site stopped pointing at would keep its entry in the gate's
    table, refuse nothing, and be covered by no pair. That is the state where
    the table reads as a boundary and is a list.
    """
    assert sorted(set(gate.FAMILIES) - {pair.family for pair in PAIRS}) == []
