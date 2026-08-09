"""The schema of issue #24, held to the refusals it exists to make.

The two the issue's done-when names are a key the schema does not admit and a
required key the document does not carry, and both have to name the key rather
than only saying no. Each is written twice here: once with a key nobody could
mistake for a valid one, and once as the near miss, which is a key differing
from a valid one by a single character. The near miss is the one worth the
effort, because it is the mistake somebody actually makes and the one a lenient
reader is most tempted to accept.

The document below is well formed and is a fixture rather than a theory. The
four theory documents of issue #29 are not in the tree, so nothing here claims
anything about them; what these tests measure is the schema, and a fixture
vocabulary is a fixture vocabulary.
"""

import copy
import json
from typing import Any

from rechenstrasse.document import schema


def a_document() -> dict[str, Any]:
    """A document in the shape the schema admits, built fresh for each test.

    General relativity with a cosmological constant, which is the smallest
    member of the covered class of record 0003. Built by a function rather than
    held as a constant, so a test that edits one key cannot change what the next
    test reads.
    """
    return {
        "schema_version": schema.CURRENT_SCHEMA_VERSION,
        "metadata": {
            "identifier": "general-relativity-with-lambda",
            "name": "General relativity with a cosmological constant",
            "citation": "a fixture, and not a claim about any published source",
        },
        "manifold": {"dimension": 4, "signature": "(-, +, +, +)"},
        "fields": [
            {"symbol": "g", "role": "metric", "symmetries": ["symmetric"]},
        ],
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


def rules(found: tuple[schema.Refusal, ...]) -> list[str]:
    return sorted(refusal.rule for refusal in found)


def named(found: tuple[schema.Refusal, ...], rule: str) -> list[str]:
    return sorted(refusal.named for refusal in found if refusal.rule == rule)


def test_a_document_in_shape_is_refused_for_nothing() -> None:
    """The floor under every other test here.

    A schema that refused this document would make the refusals below pass for
    the wrong reason, and there would be no way to tell from the assertions.
    """
    assert schema.refusals(a_document()) == ()


def test_an_unknown_key_is_refused_with_the_key_named() -> None:
    document = a_document()
    document["renormalisation"] = "whatever this was meant to do"
    found = schema.refusals(document)
    assert rules(found) == ["unknown-key"]
    assert named(found, "unknown-key") == ["renormalisation"]
    assert "renormalisation" in found[0].detail


def test_a_key_one_character_from_a_valid_one_is_refused_rather_than_read() -> None:
    """The near miss for the unknown key, at the top level.

    `lagrangean` is the spelling half the literature uses, and a reader that
    accepted it while looking for `lagrangian` would drop every term in the
    document and derive the field equations of an empty action. Nothing about
    that failure looks like a failure.
    """
    document = a_document()
    document["lagrangean"] = document.pop("lagrangian")
    found = schema.refusals(document)
    assert rules(found) == ["missing-key", "unknown-key"]
    assert named(found, "unknown-key") == ["lagrangean"]
    assert named(found, "missing-key") == ["lagrangian"]


def test_an_unknown_key_inside_a_section_names_where_it_sits() -> None:
    """A key can be valid somewhere and unknown here, so the place is part of it."""
    document = a_document()
    document["manifold"]["dimensions"] = 4
    found = schema.refusals(document)
    assert rules(found) == ["unknown-key"]
    assert found[0].named == "dimensions"
    assert found[0].where == "manifold.dimensions"


def test_an_unknown_key_inside_a_list_member_names_its_index() -> None:
    document = a_document()
    document["fields"].append(
        {
            "symbol": "phi",
            "role": "scalar",
            "symmetries": [],
            "sign": "the one the author meant",
        }
    )
    found = schema.refusals(document)
    assert rules(found) == ["unknown-key"]
    assert found[0].where == "fields[1].sign"


def test_a_missing_required_key_is_refused_with_that_key_named() -> None:
    document = a_document()
    del document["matter"]
    found = schema.refusals(document)
    assert rules(found) == ["missing-key"]
    assert named(found, "missing-key") == ["matter"]
    assert "matter" in found[0].detail


def test_a_missing_required_key_inside_a_section_is_refused_too() -> None:
    document = a_document()
    del document["metadata"]["citation"]
    found = schema.refusals(document)
    assert rules(found) == ["missing-key"]
    assert found[0].where == "metadata.citation"


def test_an_open_bound_is_written_rather_than_left_out() -> None:
    """`null` and absent are different statements, and only one is admitted.

    A parameter with no upper bound says so. A parameter whose upper bound key
    is missing is a document whose author did not say, and reading the second as
    the first is how a range nobody claimed ends up quoted as one they did.
    """
    document = a_document()
    del document["parameters"][0]["maximum"]
    found = schema.refusals(document)
    assert rules(found) == ["missing-key"]
    assert found[0].where == "parameters[0].maximum"


def test_every_reason_is_reported_rather_than_the_first() -> None:
    document = a_document()
    del document["matter"]
    del document["regime"]
    document["extra"] = 1
    found = schema.refusals(document)
    assert rules(found) == ["missing-key", "missing-key", "unknown-key"]
    assert named(found, "missing-key") == ["matter", "regime"]


def test_a_value_of_the_wrong_kind_is_refused() -> None:
    document = a_document()
    document["manifold"]["dimension"] = "four"
    found = schema.refusals(document)
    assert rules(found) == ["wrong-kind"]
    assert found[0].where == "manifold.dimension"


def test_a_boolean_is_not_read_as_a_number() -> None:
    """The near miss for the kind check.

    A boolean is an integer in this language, so a dimension written `true`
    passes an `isinstance` check that did not say otherwise, and the manifold
    the pipeline then works on is one dimensional.
    """
    document = a_document()
    document["manifold"]["dimension"] = True
    found = schema.refusals(document)
    assert rules(found) == ["wrong-kind"]
    assert found[0].where == "manifold.dimension"


def test_a_list_member_of_the_wrong_kind_is_refused() -> None:
    document = a_document()
    document["fields"][0]["symmetries"] = ["symmetric", 2]
    found = schema.refusals(document)
    assert rules(found) == ["wrong-kind"]
    assert found[0].where == "fields[0].symmetries[1]"


def test_a_list_of_something_other_than_mappings_is_refused() -> None:
    document = a_document()
    document["fields"] = ["g"]
    found = schema.refusals(document)
    assert rules(found) == ["wrong-kind"]
    assert found[0].where == "fields[0]"


def test_a_term_head_the_schema_has_no_case_for_is_refused_with_the_head_named() -> (
    None
):
    """Record 0004 places this refusal in this issue and says why.

    The alternative it rules out is handing the text to an expression parser to
    see what happens, which is a small interpreter, and a term it reads as
    something other than what the author meant is the failure this board exists
    to remove.

    A head this schema admits is not the same thing as a term this pipeline will
    answer for. `horndeski_g5` is admitted here and refused by the gate of issue
    #26, with the reason record 0003 gives, and that is a better thing to tell
    an author than that they made a typing mistake.
    """
    document = a_document()
    document["lagrangian"]["terms"].append(
        {"head": "matter_lagrangian", "coefficient": "alpha"}
    )
    found = schema.refusals(document)
    assert rules(found) == ["unknown-term-head"]
    assert found[0].named == "matter_lagrangian"
    assert found[0].where == "lagrangian.terms[2].head"
    assert "matter_lagrangian" in found[0].detail


def test_a_term_head_one_character_from_an_admitted_one_is_refused() -> None:
    """The near miss for the head, and the reason the set is closed.

    `ricci_scaler` is one character from `ricci_scalar` and is the spelling a
    tired author writes. Nothing about the term is unusual, so a reader that
    accepted it would carry a term this pipeline has no case for straight into
    the algebra.
    """
    document = a_document()
    document["lagrangian"]["terms"][0] = {
        "head": "ricci_scaler",
        "coefficient": "one_over_two_kappa",
    }
    found = schema.refusals(document)
    assert rules(found) == ["unknown-term-head"]
    assert found[0].named == "ricci_scaler"


def test_every_admitted_head_is_admitted() -> None:
    """The other direction, so the head check is not passing by refusing all of them."""
    document = a_document()
    document["lagrangian"]["terms"] = [
        {"head": head, "coefficient": "c"} for head in schema.TERM_HEADS
    ]
    assert schema.refusals(document) == ()


def test_a_version_this_build_does_not_read_is_refused_with_the_version_named() -> None:
    document = a_document()
    document["schema_version"] = schema.CURRENT_SCHEMA_VERSION + 1
    found = schema.refusals(document)
    assert rules(found) == ["unknown-schema-version"]
    assert found[0].named == str(schema.CURRENT_SCHEMA_VERSION + 1)


def test_the_current_version_is_one_this_build_reads() -> None:
    assert schema.CURRENT_SCHEMA_VERSION in schema.READABLE_SCHEMA_VERSIONS


def test_something_that_is_not_a_mapping_is_not_a_document() -> None:
    found = schema.refusals(["a list of what, exactly"])
    assert rules(found) == ["not-a-document"]
    assert found[0].named == "list"


def test_bytes_that_are_not_readable_at_all_are_refused_by_the_reader() -> None:
    loaded, found = schema.read("{ this is not a document")
    assert loaded is None
    assert rules(found) == ["not-a-document"]


def test_the_reader_returns_the_plain_data_and_the_refusals_together() -> None:
    document = a_document()
    loaded, found = schema.read(json.dumps(document))
    assert loaded == document
    assert found == ()


def test_the_reader_constructs_nothing_but_plain_data() -> None:
    """Record 0004's condition on the input, as an assertion over what came back.

    Every value that survives the reader is a string, a number, a boolean, null,
    a list or a mapping. Nothing in a document names a type, so there is no key
    an author could write that would put anything else in this walk.
    """
    plain = (str, int, float, bool, dict, list, type(None))
    loaded, _ = schema.read(json.dumps(a_document()))

    def every_value(value: object) -> list[object]:
        if isinstance(value, dict):
            return [value, *[v for m in value.values() for v in every_value(m)]]
        if isinstance(value, list):
            return [value, *[v for m in value for v in every_value(m)]]
        return [value]

    assert all(isinstance(value, plain) for value in every_value(loaded))


def test_reading_a_document_does_not_change_it() -> None:
    """The schema reads and does not repair, which is what makes a hash mean something.

    Record 0007 requires a run to record the hash of its input, and that means
    something only if the thing the pipeline worked on is the thing on disk.
    """
    document = a_document()
    before = copy.deepcopy(document)
    schema.refusals(document)
    assert document == before
