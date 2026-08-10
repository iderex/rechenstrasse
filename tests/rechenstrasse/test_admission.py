"""The seam between the gate and the first stage that computes.

Issue #26's last clause: no stage after the gate can be reached without passing
it. Nothing could hold that while the stage took an action, because an action is
what the reader builds out of bytes and the gate never sees one, so a caller
holding an action walks past the gate without writing anything that looks like a
mistake.

What is asserted here. That every document in the tree comes back admitted and
carries the verdict it was admitted on, so what the gate did not evaluate
travels with the thing that reaches the algebra. That a refused document and an
unplaceable one come back as neither, with the gate's verdict and no reader
refusals. That a document the reader never turned into an action comes back with
the reader's refusals and no verdict, because a typing mistake and a theory being
ruled out are different things to be told. And that the stage will not take an
action.

What no leg here asserts. `Admitted` is a frozen dataclass and Python lets
anybody build one, so nothing below is evidence that the stage cannot be reached
by a caller who decided to. What is claimed is that it cannot be reached by
accident, and the two suites of the variation stage build the value by hand in
one named helper each, where the arms they reach exist for inputs no document
has.
"""

import json
from pathlib import Path

import pytest

from rechenstrasse.admissibility import admission, gate
from rechenstrasse.document import reader
from rechenstrasse.variation import metric

ROOT = Path(__file__).resolve().parents[2]
THEORIES = ROOT / "theories"

STEMS = sorted(path.stem for path in THEORIES.glob("*.json"))

# The documents that declare a scalar field. The edit that puts a document in a
# refused family below adds a term built from one, so a document declaring none
# is refused by the reader for the reference rather than by the gate for the
# family, and the leg about the order is where that case is held.
WITH_A_SCALAR = sorted(
    path.stem
    for path in THEORIES.glob("*.json")
    if any(
        member["role"] == "scalar"
        for member in json.loads(path.read_text(encoding="utf-8"))["fields"]
    )
)


def text_of(stem: str) -> str:
    return (THEORIES / f"{stem}.json").read_text(encoding="utf-8")


def edited(stem: str, change: object) -> str:
    """One document with one edit in it, written back out as bytes.

    The bytes rather than the mapping, because `admit` starts at the bytes and a
    leg that handed it a mapping would be testing something else.
    """
    document = json.loads(text_of(stem))
    assert callable(change)
    change(document)
    return json.dumps(document)


def test_the_tree_holds_documents_to_admit() -> None:
    assert STEMS, f"no theory document below {THEORIES}, which is not a pass"


@pytest.mark.parametrize("stem", STEMS)
def test_a_document_in_the_tree_is_admitted_with_its_verdict(stem: str) -> None:
    """Covered, and the verdict travels with the action rather than beside it.

    A stage that took the action alone would leave a caller to carry the list of
    what the gate did not evaluate, and a list of assumptions carried beside a
    result is one that gets dropped.
    """
    passed = admission.admit(text_of(stem))
    assert isinstance(passed, admission.Admitted), (stem, passed)
    assert passed.verdict.state == gate.COVERED
    assert passed.verdict.reaches_the_next_stage()
    assert passed.action.metadata.identifier == stem


def test_the_scalar_theories_carry_what_the_gate_did_not_decide_into_the_stage() -> (
    None
):
    """The narrower covered verdict reaches the algebra rather than stopping short.

    Record 0003 refuses a scalar whose mass puts the range of the extra force
    inside the regime being asked about, and the gate does not decide it. A
    document declaring a scalar is admitted with that entry, and this is the leg
    that says the entry got past the seam.
    """
    with_a_scalar = [
        stem
        for stem in STEMS
        if any(declared.role == "scalar" for declared in _admitted(stem).action.fields)
    ]
    assert with_a_scalar, "no document here declares a scalar field"
    for stem in with_a_scalar:
        passed = _admitted(stem)
        assert gate.SCALAR_FORCE_RANGE in [
            reason.about for reason in passed.verdict.not_evaluated
        ]


def _admitted(stem: str) -> admission.Admitted:
    passed = admission.admit(text_of(stem))
    assert isinstance(passed, admission.Admitted), (stem, passed)
    return passed


def widen(document: dict[str, object]) -> None:
    """The edit an author widening a document actually makes.

    One term head away from the covered Horndeski sector is the sector record
    0003 refuses for its derivative couplings.
    """
    terms = document["lagrangian"]["terms"]  # type: ignore[index]
    terms.append({"head": "horndeski_g5", "coefficient": "G5_of_phi_and_X"})


@pytest.mark.parametrize("stem", WITH_A_SCALAR)
def test_a_refused_document_does_not_come_back_admitted(stem: str) -> None:
    """The theory is what was refused, so the gate is what answered.

    The value that comes back carries the gate's verdict and no reader refusals,
    because the bytes were a document and it is the theory they describe that is
    outside the covered class.
    """
    stopped = admission.admit(edited(stem, widen))
    assert isinstance(stopped, admission.NotAdmitted), stem
    assert stopped.refusals == ()
    assert stopped.verdict is not None
    assert stopped.verdict.state == gate.REFUSED


def test_the_reader_answers_first_where_both_would_have_something_to_say() -> None:
    """The order in the seam, and what it costs, measured rather than assumed.

    The same edit on a document declaring no scalar field is a term built from a
    field that document never declares, which the reader refuses before the gate
    sees anything. So this document comes back with a reference the author has to
    fix and not with the family name, and the two are not the same sentence.

    The order is the one the seam commits to: bytes that are not a theory have no
    theory for the gate to place, and a family named for a document that never
    resolved would be a statement about something nobody wrote. What it costs is
    that an author making both mistakes at once is told about the reference and
    finds out about the family on the next run.
    """
    without = [stem for stem in STEMS if stem not in WITH_A_SCALAR]
    assert without, "every document here declares a scalar, so this leg is empty"
    stopped = admission.admit(edited(without[0], widen))
    assert isinstance(stopped, admission.NotAdmitted)
    assert stopped.verdict is None
    assert [refusal.rule for refusal in stopped.refusals] == ["undeclared-field"]


def test_an_unplaceable_document_does_not_come_back_admitted() -> None:
    """The state that is refused as well and is reported as its own.

    A document in the other signature matches no family record 0003 names, so
    folding it in with the one above would tell its author their theory was ruled
    out by name when it was not.
    """

    def flip(document: dict[str, object]) -> None:
        document["manifold"]["signature"] = "(+, -, -, -)"  # type: ignore[index]

    stopped = admission.admit(edited(STEMS[0], flip))
    assert isinstance(stopped, admission.NotAdmitted)
    assert stopped.verdict is not None
    assert stopped.verdict.state == gate.UNPLACEABLE


def test_bytes_that_never_became_an_action_carry_the_reader_refusals() -> None:
    """The reader's refusal and the gate's verdict are not the same statement.

    A document with a mistake in it never became a theory, so there is no verdict
    to give about the theory, and a value carrying one would be saying the gate
    placed something it never saw.
    """
    stopped = admission.admit("{")
    assert isinstance(stopped, admission.NotAdmitted)
    assert stopped.verdict is None
    assert stopped.refusals != ()
    assert all(isinstance(refusal, reader.Refusal) for refusal in stopped.refusals)


def test_the_stage_after_the_gate_will_not_take_an_action() -> None:
    """The clause, at run time. The static half is what `typecheck` decides.

    Handing the stage what the reader produced fails rather than deriving
    anything. This is the shape of the code rather than a refusal with a reason,
    which is what `rechenstrasse.admissibility.admission` says it is: it stops a
    caller who reached for the wrong value, and it does not stop one who built
    the right value around a document the gate never saw.
    """
    action, refusals = reader.read(text_of(STEMS[0]))
    assert refusals == ()
    with pytest.raises(AttributeError):
        metric.derive(action)  # type: ignore[arg-type]


@pytest.mark.parametrize("stem", STEMS)
def test_what_the_stage_derives_is_what_the_admitted_document_says(stem: str) -> None:
    """The seam changed the route and not the answer.

    The action inside the admitted value is the one the reader builds from the
    same bytes, so a seam that quietly handed the stage a different action would
    be caught here rather than showing up as a field equation for another theory.
    """
    action, refusals = reader.read(text_of(stem))
    assert refusals == ()
    assert _admitted(stem).action == action
