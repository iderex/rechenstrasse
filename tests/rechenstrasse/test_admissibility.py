"""The gate of issue #26, held to the three states record 0003 asks for.

The assertions here are the ones that move if the boundary moves. A covered
document reaching the next stage, a refused one not reaching it, an unplaceable
one not reaching it either and not being reported as the second, and every
refused family firing on a document that is in it.

Two properties are asserted over the vocabularies rather than over a document,
because they are what stops the accepted surface and the refused surface from
drifting apart between changes: every term head the schema admits is one the
gate has a case for, and every family record 0003 names is reachable from some
document.

The documents below are fixtures and not theories. The four theory documents of
issue #29 are not in the tree, so nothing here says anything about them.
"""

from typing import Any

import pytest

from rechenstrasse.admissibility import gate
from rechenstrasse.document import schema


def a_document() -> dict[str, Any]:
    """General relativity with a cosmological constant, in the covered class."""
    return {
        "schema_version": schema.CURRENT_SCHEMA_VERSION,
        "metadata": {
            "identifier": "general-relativity-with-lambda",
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


def with_scalar() -> dict[str, Any]:
    """The same document with one scalar field, which the covered class carries."""
    document = a_document()
    document["fields"].append({"symbol": "phi", "role": "scalar", "symmetries": []})
    document["lagrangian"]["terms"].append(
        {"head": "horndeski_g2", "coefficient": "G2"}
    )
    return document


def families(verdict: gate.Verdict) -> list[str]:
    return sorted(reason.about for reason in verdict.reasons)


def test_a_covered_document_is_covered_and_reaches_the_next_stage() -> None:
    verdict = gate.classify(a_document())
    assert verdict.state == gate.COVERED
    assert verdict.reaches_the_next_stage()


def test_a_covered_verdict_states_its_reasons_rather_than_an_absent_objection() -> None:
    """Record 0003's own wording, as an assertion.

    A gate that passes what it did not recognise is a gate whose green result
    carries no information, so a covered verdict that carried no reason would be
    the failure rather than the pass.
    """
    verdict = gate.classify(a_document())
    assert verdict.reasons != ()
    assert "manifold" in families(verdict)
    assert "lagrangian" in families(verdict)


@pytest.mark.parametrize(
    ("head", "family"),
    sorted(gate.HEAD_FAMILIES.items()),
)
def test_a_term_from_a_refused_family_is_refused_by_that_family(
    head: str, family: str
) -> None:
    document = a_document()
    document["lagrangian"]["terms"].append({"head": head, "coefficient": "c"})
    verdict = gate.classify(document)
    assert verdict.state == gate.REFUSED
    assert families(verdict) == [family]
    assert not verdict.reaches_the_next_stage()


@pytest.mark.parametrize(("role", "family"), sorted(gate.ROLE_FAMILIES.items()))
def test_a_field_from_a_refused_family_is_refused_by_that_family(
    role: str, family: str
) -> None:
    document = a_document()
    document["fields"].append({"symbol": "A", "role": role, "symmetries": []})
    verdict = gate.classify(document)
    assert verdict.state == gate.REFUSED
    assert families(verdict) == [family]


def test_the_refusal_carries_the_reason_record_0003_gives() -> None:
    """The record's own argument rather than a paraphrase of it.

    A refusal that reworded the reason would drift from the record, and a reader
    who went to the record to check would find two arguments that are nearly the
    same, which is the state that takes longest to resolve.
    """
    document = a_document()
    document["lagrangian"]["terms"].append(
        {"head": "horndeski_g5", "coefficient": "G5"}
    )
    verdict = gate.classify(document)
    assert gate.FAMILIES["derivative-coupling"] in verdict.reasons[0].detail


def test_a_second_metric_is_refused_even_where_the_role_is_spelled_the_same() -> None:
    """The near miss for the second metric.

    A bimetric document does not have to declare a role called `second_metric`.
    The honest way to write one is two fields that both say `metric`, and a gate
    reading roles one at a time accepts it, because each field on its own is
    inside the covered class.
    """
    document = a_document()
    document["fields"].append(
        {"symbol": "f", "role": "metric", "symmetries": ["symmetric"]}
    )
    verdict = gate.classify(document)
    assert verdict.state == gate.REFUSED
    assert families(verdict) == ["second-metric"]


def test_a_second_scalar_is_unplaceable_rather_than_refused() -> None:
    """Outside the covered class and inside no named family, which is the third state.

    The covered class carries at most one additional scalar. Two is not a family
    record 0003 refuses by name, so folding it into the second state would tell
    its author something that is not true.
    """
    document = with_scalar()
    document["fields"].append({"symbol": "chi", "role": "scalar", "symmetries": []})
    verdict = gate.classify(document)
    assert verdict.state == gate.UNPLACEABLE
    assert not verdict.reaches_the_next_stage()


def test_a_dimension_other_than_four_is_unplaceable() -> None:
    document = a_document()
    document["manifold"]["dimension"] = 5
    verdict = gate.classify(document)
    assert verdict.state == gate.UNPLACEABLE
    assert families(verdict) == ["dimension"]


def test_another_signature_is_unplaceable_rather_than_read_anyway() -> None:
    """The near miss for the conventions.

    The other signature convention is as common in the literature as this one,
    and a document written in it is not wrong, it is written somewhere else.
    Reading it as if it were written here flips signs that do not announce
    themselves.
    """
    document = a_document()
    document["manifold"]["signature"] = "(+, -, -, -)"
    verdict = gate.classify(document)
    assert verdict.state == gate.UNPLACEABLE
    assert families(verdict) == ["signature"]


def test_a_role_the_gate_has_no_case_for_is_unplaceable() -> None:
    document = a_document()
    document["fields"].append({"symbol": "psi", "role": "spinor", "symmetries": []})
    verdict = gate.classify(document)
    assert verdict.state == gate.UNPLACEABLE
    assert families(verdict) == ["field-role"]


def test_a_document_that_is_not_in_the_shape_of_the_schema_is_unplaceable() -> None:
    """A gate cannot classify what it cannot read, and says so rather than passing."""
    document = a_document()
    del document["lagrangian"]
    verdict = gate.classify(document)
    assert verdict.state == gate.UNPLACEABLE
    assert families(verdict) == ["not-readable"]


def test_something_that_is_not_a_document_at_all_is_unplaceable() -> None:
    verdict = gate.classify("an action, honestly")
    assert verdict.state == gate.UNPLACEABLE
    assert not verdict.reaches_the_next_stage()


def test_a_family_wins_over_being_unplaceable() -> None:
    """Both true at once, and the author is told the more useful of the two."""
    document = a_document()
    document["manifold"]["dimension"] = 5
    document["lagrangian"]["terms"].append(
        {"head": "gauss_bonnet", "coefficient": "alpha"}
    )
    verdict = gate.classify(document)
    assert verdict.state == gate.REFUSED
    assert families(verdict) == ["quadratic-curvature"]


def test_every_head_the_schema_admits_is_one_the_gate_has_a_case_for() -> None:
    """What keeps the accepted surface and the refused surface moving together.

    Record 0004 fixes the route the schema grows by: a schema version carrying a
    new term and the matching case in this gate, in one change. A head admitted
    by the schema that this gate had never heard of is that rule broken, and it
    is the shape nobody notices, because the document parses and the run
    continues.
    """
    classified = set(gate.COVERED_HEADS) | set(gate.HEAD_FAMILIES)
    assert set(schema.TERM_HEADS) == classified


def test_a_head_the_gate_has_no_case_for_falls_closed_rather_than_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The arm behind the property above, exercised rather than assumed.

    The assertion above holds the tree as it stands. This one says what happens
    on the day somebody lands a head in the schema and forgets the gate, and the
    answer is that the document does not reach the algebra. The schema is what
    has to be widened to reach the arm, because a head it does not admit never
    gets past the reader.
    """
    monkeypatch.setitem(
        schema.TERM_HEADS, "invented", "a head landed in the schema and nowhere else"
    )
    document = a_document()
    document["lagrangian"]["terms"].append({"head": "invented", "coefficient": "c"})
    verdict = gate.classify(document)
    assert verdict.state == gate.UNPLACEABLE
    assert families(verdict) == ["term-head"]


def test_every_family_record_0003_names_is_reachable() -> None:
    """The other direction, so a family cannot sit in the table refusing nothing."""
    reachable = set(gate.HEAD_FAMILIES.values()) | set(gate.ROLE_FAMILIES.values())
    assert set(gate.FAMILIES) == reachable


def test_a_covered_verdict_names_the_property_it_did_not_decide() -> None:
    """The negative disclosure record 0003's last refusal leaves behind.

    A scalar whose mass puts the range of the extra force inside the operator's
    regime is refused by that record and is not decided here. A covered verdict
    on a document with a scalar field says so, and record 0007's provenance
    block is where that reaches the operator.
    """
    verdict = gate.classify(with_scalar())
    assert verdict.state == gate.COVERED
    assert [reason.about for reason in verdict.not_evaluated] == [
        gate.SCALAR_FORCE_RANGE
    ]


def test_a_document_with_no_scalar_has_nothing_left_undecided() -> None:
    """The property is about a scalar, so a document without one is not narrowed by it.

    Without this the list would be a constant, and a constant disclosure is one
    a reader stops reading.
    """
    assert gate.classify(a_document()).not_evaluated == ()
