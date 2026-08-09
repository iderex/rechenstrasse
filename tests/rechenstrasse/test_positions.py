"""The position index of issue #25, held to the one thing it is worth.

An index that is right most of the time is worse than none, because a reader
follows it to the wrong line and stops trusting the messages. So the assertions
here are about correctness of the position rather than about the index being
non-empty: every path it records has to point at the characters that path is
about, and a text and a value that did not come from each other have to be
refused rather than walked past.
"""

import json

import pytest

from rechenstrasse.document import positions

DOCUMENT = """{
  "schema_version": 1,
  "fields": [
    {
      "symbol": "g",
      "symmetries": ["symmetric"]
    },
    {
      "symbol": "phi",
      "symmetries": []
    }
  ],
  "regime": {"name": "solar system"},
  "count": -12.5,
  "absent": null
}
"""


def index() -> dict[str, positions.Position]:
    return positions.of(DOCUMENT)


def at(position: positions.Position) -> str:
    """What the text holds from a recorded position onwards, to the end of its line."""
    return DOCUMENT.splitlines()[position.line - 1][position.column - 1 :]


def test_every_path_the_data_can_carry_is_in_the_index() -> None:
    """The walk follows the parsed data, so the two sets are the same set.

    Written as an equality rather than as a spot check on one path, because the
    failure this guards against is a shape of value the walk forgets to descend
    into, and that shows up as a missing path and not as a wrong one.
    """
    found = index()
    loaded = json.loads(DOCUMENT)
    expected = {""}

    def paths(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key in value:
                expected.add(positions.join(path, str(key)))
                paths(value[key], positions.join(path, str(key)))
        elif isinstance(value, list):
            for number, member in enumerate(value):
                expected.add(f"{path}[{number}]")
                paths(member, f"{path}[{number}]")

    paths(loaded, "")
    assert set(found) == expected


def test_a_member_of_a_mapping_is_recorded_at_its_key() -> None:
    """Which is where the cursor belongs for a key nobody admits."""
    found = index()
    assert at(found["schema_version"]).startswith('"schema_version"')
    assert at(found["fields"]).startswith('"fields"')
    assert at(found["regime.name"]).startswith('"name"')


def test_a_member_of_a_list_is_recorded_at_the_member() -> None:
    """It has no key, so the member itself is the only thing to point at."""
    found = index()
    assert at(found["fields[0]"]).startswith("{")
    assert at(found["fields[0].symmetries[0]"]).startswith('"symmetric"')


def test_a_position_deep_in_the_document_carries_the_line_it_is_on() -> None:
    """The whole point of the index, as a number a reader can act on."""
    found = index()
    assert found["fields[1].symbol"].line == 9
    assert DOCUMENT.splitlines()[8].strip().startswith('"symbol": "phi"')


def test_numbers_and_the_bare_words_are_walked_past_rather_than_read() -> None:
    """A literal is skipped by where it ends, and the three kinds end alike."""
    found = index()
    assert at(found["count"]).startswith('"count"')
    assert at(found["absent"]).startswith('"absent"')


def test_the_document_as_a_whole_is_recorded_at_its_first_character() -> None:
    assert index()[""] == positions.Position(line=1, column=1)


def test_a_path_the_document_does_not_carry_resolves_to_the_part_above_it() -> None:
    """A required key that is absent has no position, and its mapping does."""
    found = index()
    assert positions.nearest(found, "regime.length_scale") == found["regime"]
    assert positions.nearest(found, "fields[0].role") == found["fields[0]"]


def test_a_path_with_nothing_above_it_resolves_to_the_document() -> None:
    found = index()
    assert positions.nearest(found, "matter") == found[""]


def test_bytes_the_loader_refuses_are_indexed_at_the_place_it_stopped() -> None:
    """So a refusal about something that is not a document still names a line."""
    found = positions.of('{\n  "schema_version": 1,\n  "fields": [\n}\n')
    assert set(found) == {""}
    assert found[""].line == 4
    assert positions.nearest(found, "lagrangian.terms[3].head") == found[""]


def test_a_text_and_a_value_that_did_not_come_from_each_other_are_refused() -> None:
    """The proof that the two are held in step.

    Reached by handing the walk a value the text does not hold. Nothing in the
    pipeline can do that, which is the point: the arm exists so that a walk that
    silently drifted would fail here rather than report a confident wrong line.
    """
    with pytest.raises(positions.Desynchronised):
        positions.positions({"schema_version": 1, "invented": 2}, DOCUMENT)


def test_a_value_that_ends_before_the_text_does_is_refused() -> None:
    with pytest.raises(positions.Desynchronised):
        positions.positions(1, DOCUMENT)


def test_an_unterminated_string_is_refused_rather_than_run_off_the_end() -> None:
    with pytest.raises(positions.Desynchronised):
        positions.positions(["unterminated"], '["unterminated]')


def test_an_escape_at_the_end_of_the_text_is_refused() -> None:
    with pytest.raises(positions.Desynchronised):
        positions.positions(["x"], '["x\\')


def test_a_literal_that_is_not_there_is_refused() -> None:
    with pytest.raises(positions.Desynchronised):
        positions.positions([1], "[]")


def test_an_escaped_quote_inside_a_key_does_not_end_the_string() -> None:
    """The one place a naive scan drifts, and it drifts silently.

    A key holding an escaped quote is legal and rare, which is the combination
    that stays wrong for a long time: the walk would take the escaped quote as
    the end of the key and every position after it would be off.
    """
    text = '{"a\\"b": 1, "c": 2}'
    found = positions.positions(json.loads(text), text)
    assert set(found) == {"", 'a"b', "c"}
    assert found["c"].column == text.index('"c"') + 1
