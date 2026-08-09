"""The reader of issue #25, held to the four things its Done-when asks for.

Every theory document in the tree parses. A round trip through emit and parse is
equal on all of them. A malformed document produces a refusal naming the
location. And the reader reaches into no later stage, which is asserted over the
module's own imports rather than trusted.

The refusals this reader adds are the ones neither the schema nor the gate makes,
and each is paired here with the document one edit away from it that has to pass.
A refusal that fires on everything nearby says nothing about the boundary it
claims to draw, and the near miss is where that is decided.
"""

import ast
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from rechenstrasse import representation
from rechenstrasse.document import reader, schema

ROOT = Path(__file__).resolve().parents[2]
THEORIES = ROOT / "theories"

# The stages this reader may not reach into. Issue #25 names the variation and
# expansion stages, and the seam is here for record 0005's own reason: nothing
# above it may import from whatever implements canonicalisation.
LATER_STAGES = (
    "rechenstrasse.variation",
    "rechenstrasse.ppn",
    "rechenstrasse.canonical",
    "rechenstrasse.perturbation",
)


def theory_documents() -> list[tuple[str, str]]:
    """Every theory document in the tree, by file name stem, as its own bytes."""
    return [
        (path.stem, path.read_text(encoding="utf-8"))
        for path in sorted(THEORIES.glob("*.json"))
    ]


def a_document() -> dict[str, Any]:
    """A covered document, in the shape of the schema, built here and not read."""
    return {
        "schema_version": schema.CURRENT_SCHEMA_VERSION,
        "metadata": {
            "identifier": "a-fixture",
            "name": "A fixture",
            "citation": "a fixture, and not a claim about any published source",
        },
        "manifold": {"dimension": 4, "signature": "(-, +, +, +)"},
        "fields": [
            {"symbol": "g", "role": "metric", "symmetries": ["symmetric"]},
            {"symbol": "phi", "role": "scalar", "symmetries": []},
        ],
        "lagrangian": {
            "terms": [
                {"head": "ricci_scalar", "coefficient": "one_over_two_kappa"},
                {"head": "horndeski_g2", "coefficient": "G2"},
            ]
        },
        "matter": {"coupling": "minimal", "frame": "jordan"},
        "parameters": [
            {
                "symbol": "omega",
                "minimum": None,
                "maximum": None,
                "claimed_by": "a fixture",
            }
        ],
        "regime": {"name": "solar system", "length_scale": "astronomical unit"},
    }


def written(document: dict[str, Any]) -> str:
    """A document as the bytes a reader is given, laid out over several lines.

    Several lines rather than one, because a refusal is asserted here to name a
    line and a one line document makes every such assertion pass.
    """
    return json.dumps(document, indent=2) + "\n"


def refusals(document: dict[str, Any]) -> tuple[reader.Refusal, ...]:
    action, found = reader.read(written(document))
    assert action is None
    return found


def rules(found: tuple[reader.Refusal, ...]) -> list[str]:
    return sorted(refusal.rule for refusal in found)


def test_every_theory_document_in_the_tree_parses() -> None:
    """The first clause of the Done-when, over the directory and not over four names."""
    stems = theory_documents()
    assert stems, "no theory document in the tree, which is the wrong root"
    for stem, text in stems:
        action, found = reader.read(text)
        assert found == (), f"{stem} was refused: {[str(one) for one in found]}"
        assert action is not None
        assert action.metadata.identifier != ""


def test_a_round_trip_through_emit_and_parse_is_equal_on_all_of_them() -> None:
    """The second clause, as an equality on the representation and not on the bytes."""
    for stem, text in theory_documents():
        action, _ = reader.read(text)
        assert action is not None
        again, found = reader.read(reader.emit(action))
        assert found == (), f"{stem} did not survive a round trip"
        assert again == action


def test_a_round_trip_carries_a_bound_that_is_written_rather_than_absent() -> None:
    """The one field where a number and its absence are different statements.

    Every document in the tree writes null on both sides today, so the property
    would hold by accident. This is the document that has one.
    """
    document = a_document()
    document["parameters"][0]["minimum"] = 40000
    action, _ = reader.read(written(document))
    assert action is not None
    assert action.parameters[0].minimum == 40000
    assert action.parameters[0].maximum is None
    again, found = reader.read(reader.emit(action))
    assert found == ()
    assert again == action


def test_the_emitted_document_is_read_by_the_schema_as_well() -> None:
    """What emit writes is a document and not only something this reader accepts."""
    action, _ = reader.read(written(a_document()))
    assert action is not None
    assert schema.read(reader.emit(action))[1] == ()


def test_a_mention_resolves_to_the_declaration_and_not_to_a_copy_of_it() -> None:
    """Record 0005's rule, as an identity rather than as an equality.

    Two equal declarations would pass an equality here and still be the failure
    the record is about, because a stage holding one of them could be reading a
    symmetry the other does not carry.
    """
    action, _ = reader.read(written(a_document()))
    assert action is not None
    metric = action.declaration("g")
    scalar = action.declaration("phi")
    assert metric is not None and scalar is not None
    ricci, g2 = action.lagrangian.terms
    assert ricci.mentions[0] is metric
    assert g2.mentions == (metric, scalar)
    assert metric.symmetries == ("symmetric",)
    assert metric.slots == 2


def test_asking_for_a_symbol_no_field_declares_gives_nothing_back() -> None:
    """Nothing rather than a declaration built on the spot.

    A lookup that invented one would put an object in an expression that the
    document never declared, which is the same failure as resolving a mention
    to the wrong declaration, arriving from the other side.
    """
    action, _ = reader.read(written(a_document()))
    assert action is not None
    assert action.declaration("psi") is None


def test_the_terms_stay_in_the_order_the_document_wrote_them() -> None:
    """Reordering is canonicalisation, which issue #25 puts outside this stage."""
    document = a_document()
    document["lagrangian"]["terms"].reverse()
    action, _ = reader.read(written(document))
    assert action is not None
    assert [term.head for term in action.lagrangian.terms] == [
        "horndeski_g2",
        "ricci_scalar",
    ]


def test_a_document_the_schema_refuses_is_refused_with_the_schema_s_own_rule() -> None:
    """One vocabulary for the caller, and the location the schema does not carry."""
    document = a_document()
    del document["matter"]
    found = refusals(document)
    assert rules(found) == ["missing-key"]
    assert found[0].where == "matter"
    # A key the whole document is missing has nothing above it but the document,
    # so this is the one refusal whose location is the first character. The case
    # below is the one where pointing somewhere is worth something.
    assert found[0].at.line == 1


def test_a_key_missing_from_a_mapping_points_at_that_mapping() -> None:
    """The nearest true place, which is also where the cursor belongs."""
    document = a_document()
    del document["manifold"]["signature"]
    text = written(document)
    found = reader.read(text)[1]
    assert rules(found) == ["missing-key"]
    assert found[0].where == "manifold.signature"
    assert text.splitlines()[found[0].at.line - 1].lstrip().startswith('"manifold"')


def test_an_unknown_key_names_the_line_the_key_is_on() -> None:
    """The clause the whole position index exists for.

    Asserted against the line the key was written on rather than against any
    line at all, so an index that pointed at the first line of every document
    would fail here.
    """
    document = a_document()
    document["manifold"]["orientable"] = True
    text = written(document)
    found = reader.read(text)[1]
    assert rules(found) == ["unknown-key"]
    line = text.splitlines()[found[0].at.line - 1]
    assert line.lstrip().startswith('"orientable"')
    assert line[found[0].at.column - 1 :].startswith('"orientable"')


def test_bytes_that_are_not_a_document_are_refused_where_the_loader_stopped() -> None:
    action, found = reader.read('{\n  "schema_version": 1,\n}\n')
    assert action is None
    assert rules(found) == ["not-a-document"]
    # Where the loader stopped, which is the comma and not the brace after it.
    assert (found[0].at.line, found[0].at.column) == (2, 22)
    assert found[0].where == ""


def test_a_refusal_reads_as_a_place_and_a_sentence() -> None:
    """What a person sees, which is the reason issue #25 asks for a location."""
    document = a_document()
    document["fields"][1]["symmetries"] = ["symmetric"]
    found = refusals(document)
    assert str(found[0]).startswith("line ")
    assert "at fields[1].symmetries[0]" in str(found[0])
    assert "index slots" in str(found[0])


def test_a_symbol_declared_twice_is_refused() -> None:
    document = a_document()
    document["fields"][1]["symbol"] = "g"
    found = refusals(document)
    assert rules(found) == ["symbol-declared-twice"]
    assert found[0].named == "g"


def test_a_field_and_a_parameter_under_one_symbol_are_refused_together() -> None:
    """They name objects in one expression, so one symbol is one thing across both."""
    document = a_document()
    document["parameters"][0]["symbol"] = "phi"
    found = refusals(document)
    assert rules(found) == ["symbol-declared-twice"]
    assert found[0].where == "parameters[0].symbol"


def test_two_symbols_one_character_apart_are_the_near_miss_and_pass() -> None:
    """The boundary the refusal above draws, from the side that has to stay open."""
    document = a_document()
    document["fields"][1]["symbol"] = "gg"
    action, found = reader.read(written(document))
    assert found == ()
    assert action is not None
    assert [declared.symbol for declared in action.fields] == ["g", "gg"]


def test_a_symmetry_on_a_field_with_no_slots_to_swap_is_refused() -> None:
    document = a_document()
    document["fields"][1]["symmetries"] = ["symmetric"]
    found = refusals(document)
    assert rules(found) == ["symmetry-without-slots"]
    assert found[0].where == "fields[1].symmetries[0]"


def test_the_same_symmetry_on_a_field_with_the_slots_is_the_near_miss() -> None:
    document = a_document()
    document["fields"][0]["symmetries"] = ["symmetric", "antisymmetric"]
    action, found = reader.read(written(document))
    assert found == ()
    assert action is not None
    assert action.fields[0].symmetries == ("symmetric", "antisymmetric")


def test_a_symmetry_this_representation_has_no_case_for_is_refused() -> None:
    document = a_document()
    document["fields"][0]["symmetries"] = ["symetric"]
    found = refusals(document)
    assert rules(found) == ["unknown-symmetry"]
    assert found[0].named == "symetric"


def test_a_role_with_no_slot_count_is_refused_before_the_symmetries_are_judged() -> (
    None
):
    """One refusal and not two, because the second would be a guess about the first."""
    document = a_document()
    document["fields"][1]["role"] = "spinor"
    document["fields"][1]["symmetries"] = ["symmetric"]
    found = refusals(document)
    assert rules(found) == ["unknown-role"]
    assert found[0].named == "spinor"


def test_a_term_built_from_a_field_the_document_does_not_declare_is_refused() -> None:
    """The schema admits the term and the gate places the theory. Neither asks this."""
    document = a_document()
    del document["fields"][1]
    del document["parameters"][0]
    found = refusals(document)
    assert rules(found) == ["undeclared-field"]
    assert found[0].where == "lagrangian.terms[1].head"
    assert "scalar" in found[0].detail


def test_the_gate_calls_that_document_covered_which_is_why_this_refuses_it() -> None:
    """The near miss for the refusal above, taken from the other direction.

    Without this the refusal could be read as duplicating something upstream.
    The document below reaches the algebra past both the schema and the gate,
    and it is this reader that stops it.
    """
    from rechenstrasse.admissibility import gate

    document = a_document()
    del document["fields"][1]
    del document["parameters"][0]
    assert schema.refusals(document) == ()
    assert gate.classify(document).state == gate.COVERED


def test_a_term_that_could_resolve_to_two_declarations_is_refused() -> None:
    document = a_document()
    document["fields"].append({"symbol": "chi", "role": "scalar", "symmetries": []})
    found = refusals(document)
    assert rules(found) == ["ambiguous-field"]
    assert "phi" in found[0].detail and "chi" in found[0].detail


def test_one_declaration_per_requirement_is_the_near_miss_and_resolves() -> None:
    document = a_document()
    document["fields"].append({"symbol": "chi", "role": "vector", "symmetries": []})
    action, found = reader.read(written(document))
    assert found == ()
    assert action is not None
    assert action.lagrangian.terms[1].mentions[1].symbol == "phi"


def test_a_torsional_term_resolves_against_either_torsional_role() -> None:
    """A requirement is a set of roles, and both members of this one satisfy it."""
    for role in ("tetrad", "torsion"):
        document = a_document()
        document["fields"] = [{"symbol": "e", "role": role, "symmetries": []}]
        document["lagrangian"]["terms"] = [
            {"head": "torsion_scalar", "coefficient": "f_of_T"}
        ]
        document["parameters"] = []
        action, found = reader.read(written(document))
        assert found == (), f"a document declaring {role} was refused"
        assert action is not None
        assert action.lagrangian.terms[0].mentions[0].role == role


def test_every_head_the_schema_admits_is_one_this_reader_can_resolve() -> None:
    """What keeps the accepted surface and this stage moving together.

    The gate holds the same property from its own side. A head admitted by the
    schema that this reader has nothing written for would be a term arriving in
    the representation built from nothing, and the document would parse.
    """
    assert set(schema.TERM_HEADS) == set(reader.HEAD_NEEDS)


def test_every_role_a_requirement_names_is_one_that_has_a_slot_count() -> None:
    """The other direction, so a requirement cannot name a role no field can carry."""
    wanted = {
        role for needs in reader.HEAD_NEEDS.values() for one in needs for role in one
    }
    assert wanted <= set(representation.SLOTS)


def test_a_head_this_reader_has_nothing_for_falls_closed_rather_than_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The arm behind the property above, exercised rather than argued for.

    The schema is what has to be widened to reach it, because a head it does not
    admit never gets this far, and that is the shape of the mistake: a term
    landed in the schema and nowhere else.
    """
    monkeypatch.setitem(
        schema.TERM_HEADS, "invented", "a head landed in the schema and nowhere else"
    )
    document = a_document()
    document["lagrangian"]["terms"].append({"head": "invented", "coefficient": "c"})
    found = refusals(document)
    assert rules(found) == ["unresolved-head"]
    assert found[0].named == "invented"


def test_every_refusal_this_reader_makes_carries_a_line_inside_the_document() -> None:
    """A location that points past the end of the file is not a location.

    Over every refusal this file provokes rather than over one of them, because
    the failure is a path the index cannot place, and which path that is depends
    on the refusal.
    """
    document = a_document()
    document["fields"][1]["symbol"] = "g"
    document["fields"][0]["symmetries"] = ["symetric"]
    text = written(document)
    found = reader.read(text)[1]
    assert len(found) == 2
    lines = text.splitlines()
    for refusal in found:
        assert 1 <= refusal.at.line <= len(lines)
        assert 1 <= refusal.at.column <= len(lines[refusal.at.line - 1]) + 1


def imports_of(source: str) -> set[str]:
    """Every module a source file imports, by the name written in the import line.

    A pure function of the text it is given, so the proof that it bites is a
    fixture source rather than an edit to the module it judges.
    """
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            found.add(node.module)
    return found


def reaches_a_later_stage(source: str) -> list[str]:
    return sorted(
        name
        for name in imports_of(source)
        if any(name == stage or name.startswith(stage + ".") for stage in LATER_STAGES)
    )


def test_the_reader_imports_nothing_from_the_variation_or_expansion_stages() -> None:
    """The last clause of the Done-when, read off the module rather than reviewed."""
    assert reaches_a_later_stage(inspect.getsource(reader)) == []
    assert reaches_a_later_stage(inspect.getsource(representation)) == []


def test_the_check_above_refuses_a_reader_that_did_reach_one() -> None:
    """The proof that it bites, on a source one import away from the real one."""
    planted = "from rechenstrasse.variation import metric\n" + inspect.getsource(reader)
    assert reaches_a_later_stage(planted) == ["rechenstrasse.variation"]
    assert reaches_a_later_stage("import rechenstrasse.ppn.bookkeeping\n") == [
        "rechenstrasse.ppn.bookkeeping"
    ]
    assert reaches_a_later_stage("import rechenstrasse.document.schema\n") == []


def test_the_helpers_answer_for_a_key_a_document_does_not_carry() -> None:
    """The arms that let this module read a document without an assertion per line.

    They are not reached by a document the schema accepted, which is why they
    are exercised here directly instead of being left as branches nothing takes.
    """
    assert reader.mapping({}, "metadata") == {}
    assert reader.listing({"fields": "not a list"}, "fields") == []
    assert reader.listing({"fields": ["not a mapping"]}, "fields") == []
    assert reader.text({}, "symbol") == ""
    assert reader.count({"dimension": "four"}, "dimension") == 0
    assert reader.count({"dimension": True}, "dimension") == 0
    assert reader.bound({"minimum": "one"}, "minimum") is None
    assert reader.bound({"minimum": True}, "minimum") is None
    assert reader.bound({"minimum": 3}, "minimum") == 3
    assert reader.symmetries({"symmetries": "symmetric"}) == ()
    assert reader.symmetries({"symmetries": [1, "symmetric"]}) == ("symmetric",)


def test_a_document_nested_past_the_limit_is_refused_before_the_loader_runs() -> None:
    """The crash of issue #51, as the refusal that replaced it.

    Refused before the loader rather than by catching what it raises, because
    the stack is nearly gone by the time a `RecursionError` arrives and a
    handler there is a handler running on what is left of it.
    """
    text = "[" * (reader.NESTING_LIMIT + 1) + "]" * (reader.NESTING_LIMIT + 1)
    action, found = reader.read(text)
    assert action is None
    assert rules(found) == ["too-deeply-nested"]
    assert found[0].at.column == reader.NESTING_LIMIT + 1


def test_a_document_at_the_limit_is_the_near_miss_and_reaches_the_schema() -> None:
    """One level under, which has to be read rather than refused for its depth."""
    text = "[" * reader.NESTING_LIMIT + "]" * reader.NESTING_LIMIT
    found = reader.read(text)[1]
    assert rules(found) == ["not-a-document"]


def test_a_brace_inside_a_string_nests_nothing() -> None:
    """The near miss for the depth scan, which is where a naive one gets it wrong."""
    document = a_document()
    document["metadata"]["citation"] = "[" * (reader.NESTING_LIMIT + 5)
    action, found = reader.read(written(document))
    assert found == ()
    assert action is not None


def test_a_key_written_twice_in_one_mapping_is_refused() -> None:
    """The second crash of issue #51, and a defect in the reading either way.

    The loader keeps the last of the two and says nothing, so a document
    declaring a dimension twice is read as the second one and looks like a
    document that only ever said one thing.
    """
    text = (
        '{\n  "schema_version": 1,\n  "manifold": {\n'
        '    "dimension": 4,\n    "dimension": 5\n  }\n}\n'
    )
    action, found = reader.read(text)
    assert action is None
    assert rules(found) == ["key-written-twice"]
    assert found[0].named == "dimension"
    assert found[0].at.line == 5


def test_the_same_key_in_two_different_mappings_is_the_near_miss() -> None:
    """`symbol` appears in every field and in every parameter, and that is legal."""
    action, found = reader.read(written(a_document()))
    assert found == ()
    assert action is not None
    assert len(action.fields) == 2


def test_a_duplicate_key_the_schema_does_not_admit_is_still_refused_here() -> None:
    """Because the duplicate is decided before the schema sees the document.

    The order matters and is not an accident. A document with a duplicate is one
    the position index cannot walk, so the refusal has to come out before an
    index is built rather than beside the refusals that use one.
    """
    text = '{\n  "invented": 1,\n  "invented": 2\n}\n'
    found = reader.read(text)[1]
    assert rules(found) == ["key-written-twice"]


def test_bytes_the_loader_refuses_carry_no_duplicate_this_can_see() -> None:
    """The arm that keeps this from being a second opinion about broken bytes."""
    assert reader.written_twice('{"a": 1,') == []
