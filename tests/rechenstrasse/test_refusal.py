"""The four parts of issue #28, asserted over every refusal path there is.

The assertion that matters is not that one refusal has four parts. It is that
every rule the schema refuses by and every reason the gate refuses by has an
entry, so a refusal reaching a person as a bare identifier is a red suite rather
than something noticed by whoever hit it. Both directions are asserted, because
an entry for a rule that no longer exists is prose nobody will delete.
"""

import subprocess
import sys
from typing import Any

import pytest

from rechenstrasse import refusal
from rechenstrasse.admissibility import gate
from rechenstrasse.document import schema


def a_document() -> dict[str, Any]:
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
            "terms": [{"head": "ricci_scalar", "coefficient": "one_over_two_kappa"}]
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


def every_part(one: refusal.Refusal) -> list[str]:
    return [one.what, one.breaks, one.needs, one.record]


def test_every_rule_the_schema_refuses_by_has_grounds() -> None:
    """A refusal with no entry would reach its author as an identifier.

    The set on the left is read out of the schema's own docstring vocabulary by
    hand today, because nothing in that module enumerates its rules. That is why
    the assertion below is written in both directions: an entry here for a rule
    that has gone away is as much a defect as a rule with no entry.
    """
    produced: set[str] = set()
    document = a_document()
    produced.update(one.rule for one in schema.refusals({}))
    produced.update(one.rule for one in schema.refusals(["not a mapping"]))
    _, malformed = schema.read("{ not a document")
    produced.update(one.rule for one in malformed)
    wrong = a_document()
    wrong["manifold"]["dimension"] = "four"
    wrong["schema_version"] = schema.CURRENT_SCHEMA_VERSION + 1
    wrong["invented"] = 1
    wrong["lagrangian"]["terms"][0]["head"] = "ricci_scaler"
    produced.update(one.rule for one in schema.refusals(wrong))
    assert produced == set(refusal.SCHEMA_GROUNDS)
    assert schema.refusals(document) == ()


def test_every_reason_the_gate_refuses_by_has_grounds() -> None:
    reachable = (
        set(gate.FAMILIES)
        | {"dimension", "signature", "field-role", "field-content", "term-head"}
        | {"not-readable", gate.SCALAR_FORCE_RANGE}
    )
    assert reachable == set(refusal.GATE_GROUNDS)


@pytest.mark.parametrize("rule", sorted(refusal.SCHEMA_GROUNDS))
def test_a_schema_refusal_carries_four_parts(rule: str) -> None:
    one = refusal.from_schema(
        schema.Refusal(rule=rule, where="somewhere", named="a name", detail="a detail")
    )
    assert all(part.strip() for part in every_part(one))
    assert one.record.startswith("docs/decisions/")


@pytest.mark.parametrize("about", sorted(refusal.GATE_GROUNDS))
def test_a_gate_refusal_carries_four_parts(about: str) -> None:
    one = refusal.from_reason(
        gate.Reason(about=about, where="somewhere", detail="a detail")
    )
    assert all(part.strip() for part in every_part(one))
    assert one.record.startswith("docs/decisions/")


def test_the_record_a_refusal_points_at_is_in_the_tree(
    request: pytest.FixtureRequest,
) -> None:
    """A pointer at a record that is not there is worse than no pointer.

    The paths are relative to the root, and the root is found from this file
    rather than from anybody's home directory, so this passes on a runner with
    nothing installed.
    """
    root = request.config.rootpath
    pointed = {
        grounds.record
        for grounds in (
            *refusal.SCHEMA_GROUNDS.values(),
            *refusal.GATE_GROUNDS.values(),
        )
    }
    missing = [path for path in sorted(pointed) if not (root / path).is_file()]
    assert missing == []


def test_a_refusal_names_the_family_rather_than_a_category() -> None:
    document = a_document()
    document["lagrangian"]["terms"].append(
        {"head": "horndeski_g5", "coefficient": "G5"}
    )
    refused = refusal.from_verdict(gate.classify(document))
    assert len(refused) == 1
    assert refused[0].what.startswith("derivative-coupling")


def test_a_refusal_is_neither_a_stack_trace_nor_the_word_unsupported() -> None:
    """The issue's own sentence, as an assertion over the text a person reads."""
    document = a_document()
    document["fields"].append({"symbol": "A", "role": "vector", "symmetries": []})
    text = refusal.from_verdict(gate.classify(document))[0].as_text()
    assert "unsupported" not in text.lower()
    assert "Traceback" not in text
    assert "What this breaks:" in text
    assert "What would have to exist:" in text
    assert "docs/decisions/" in text


def test_the_machine_readable_form_carries_the_same_four_parts() -> None:
    """Machine readable and readable are two views of one value, not two values.

    A parity run tells a refusal from a crash by reading this, so a form that
    could carry less than the text does is one that drifts.
    """
    document = a_document()
    document["manifold"]["dimension"] = 3
    one = refusal.from_verdict(gate.classify(document))[0]
    data = one.as_data()
    assert set(data) == {"what", "where", "breaks", "needs", "record"}
    assert all(isinstance(value, str) for value in data.values())
    assert data["needs"] == one.needs


def test_a_covered_document_produces_no_refusal() -> None:
    assert refusal.from_verdict(gate.classify(a_document())) == ()


def test_what_a_covered_verdict_did_not_decide_is_reported_in_the_same_parts() -> None:
    document = a_document()
    document["fields"].append({"symbol": "phi", "role": "scalar", "symmetries": []})
    verdict = gate.classify(document)
    assert verdict.state == gate.COVERED
    undecided = refusal.undecided(verdict)
    assert len(undecided) == 1
    assert all(part.strip() for part in every_part(undecided[0]))


def test_the_three_statuses_are_three_different_numbers() -> None:
    """The whole point of the second clause of this issue's done-when.

    A refusal and an internal error sharing a status is the case a parity run
    cannot tell apart, and it is a one-character mistake to make.
    """
    statuses = [
        refusal.EXIT_SUCCESS,
        refusal.EXIT_REFUSED,
        refusal.EXIT_INTERNAL_ERROR,
    ]
    assert len(set(statuses)) == 3
    assert refusal.EXIT_SUCCESS == 0


def test_a_refusal_maps_onto_the_refused_status_and_nothing_else_does() -> None:
    document = a_document()
    document["lagrangian"]["terms"].append(
        {"head": "gauss_bonnet", "coefficient": "alpha"}
    )
    refused = refusal.from_verdict(gate.classify(document))
    assert refusal.status_for(refused) == refusal.EXIT_REFUSED
    assert refusal.status_for(()) == refusal.EXIT_SUCCESS
    assert refusal.status_for(refused) != refusal.EXIT_INTERNAL_ERROR


@pytest.mark.slow
def test_no_command_in_this_tree_leaves_the_refused_status_yet() -> None:
    """The half of the done-when that is open, held as a measurement.

    Nothing in this tree runs a document, so no process exits with the refused
    status, and this asserts that rather than leaving the absence unstated. The
    entry point that does exist returns the usage status for a bare invocation,
    which is neither of the two statuses above. When the command of issue #59
    lands, this test is what has to change, and it says so where somebody will
    find it.
    """
    finished = subprocess.run(
        [sys.executable, "-m", "rechenstrasse"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert finished.returncode not in (
        refusal.EXIT_REFUSED,
        refusal.EXIT_INTERNAL_ERROR,
    )
