"""The gate that decides whether this pipeline will answer at all.

Issue #26, over the boundary record 0003 draws. It runs before any algebra,
because an expensive wrong answer is worse than a cheap refusal, and it puts an
input into exactly one of three states.

  covered
      The input sits inside the class record 0003 names, and the reasons it does
      are stated rather than left as the absence of an objection.

  refused
      The input matches a family that record names, and the verdict carries that
      family and the reason the record gives for it. The reason is the record's
      own, because a refusal that paraphrases the argument drifts away from it.

  unplaceable
      The gate can show neither. That is refused as well and reported as its own
      state, never folded into the second, because "this is a vector-tensor
      theory and here is why that is out" and "I do not know what this is" are
      different things to tell an author.

Silence is never a pass. Every route out of `classify` produces a verdict, and
the verdict for an input the gate did not recognise is `unplaceable` rather than
the absence of a reason.

What a covered verdict does not say. Record 0003 refuses one thing that is a
property of the input rather than of a family: a scalar whose mass puts the
range of the extra force inside the regime the operator is asking about. That
comparison is a mass against a length, and both are numbers rather than
structure, so deciding it means evaluating, which is below the boundary record
0006 draws and has no machinery in this tree. Nothing here decides it and
nothing here pretends to. A verdict carries a `not_evaluated` list, that
property is in it for every document declaring a scalar field, and the list is
what record 0007's provenance block reports as assumed rather than verified. A
covered verdict with an entry in that list is a narrower statement than a
covered verdict without one, and the difference is readable.

The gate reads a document that is in the shape of the schema in
`rechenstrasse.document.schema`, and a document that is not in that shape is
unplaceable, because a gate cannot classify what it cannot read. The two
refusals are about different things: the schema decides shape and this decides
membership, and a document can pass the first and fail the second.
"""

from dataclasses import dataclass, field
from typing import Final

from rechenstrasse.document import schema

# The three states, as constants rather than as strings typed twice.
COVERED: Final = "covered"
REFUSED: Final = "refused"
UNPLACEABLE: Final = "unplaceable"

# The dimension and the signature the covered class is written in. Record 0003
# fixes four dimensions and record 0008 fixes the signature, and a document
# declaring either differently is outside the covered class without matching any
# family the record refuses by name.
COVERED_DIMENSION: Final = 4
COVERED_SIGNATURE: Final = "(-, +, +, +)"

# The families record 0003 refuses by name, and the reason it gives for each.
# The reason is the record's argument in the record's own terms, so that a
# person who hit one can go to the record and find the same sentence.
FAMILIES: Final[dict[str, str]] = {
    "derivative-coupling": (
        "the derivative couplings put the theory in a regime where a plain "
        "post-Newtonian reading is not what an experiment measures"
    ),
    "torsional-geometry": (
        "the geometry is torsional and every variational step in this pipeline "
        "assumes the Levi-Civita connection"
    ),
    "preferred-frame": (
        "a preferred frame brings in parameters this version does not solve for"
    ),
    "second-metric": "a second metric is not in the internal representation",
    "quadratic-curvature": (
        "the extra propagating modes make the standard metric ansatz the wrong "
        "shape of solution"
    ),
}

# Which term head puts a document in which refused family. Every head the schema
# admits is either here or in the covered set below, and the suite refuses one
# that is in neither, so widening what a document may say and widening what the
# gate refuses cannot happen in two changes.
HEAD_FAMILIES: Final[dict[str, str]] = {
    "horndeski_g4_kinetic": "derivative-coupling",
    "horndeski_g5": "derivative-coupling",
    "torsion_scalar": "torsional-geometry",
    "gauss_bonnet": "quadratic-curvature",
    "ricci_squared": "quadratic-curvature",
    "riemann_squared": "quadratic-curvature",
}

# The heads that are inside the covered class, with the reason each one is.
COVERED_HEADS: Final[dict[str, str]] = {
    "ricci_scalar": "the curvature scalar with a constant coefficient",
    "cosmological_constant": "a cosmological constant on the geometry side",
    "horndeski_g2": "G2 free, which record 0003 admits",
    "horndeski_g3": "G3 free, which record 0003 admits",
    "horndeski_g4": "G4 a function of the field alone, which record 0003 admits",
}

# The roles a field may declare, and what each one means for membership. The
# schema leaves this vocabulary open, which is what makes the third state
# reachable: a role nobody here has a case for is what the gate cannot place.
COVERED_ROLES: Final[frozenset[str]] = frozenset({"metric", "scalar"})
ROLE_FAMILIES: Final[dict[str, str]] = {
    "vector": "preferred-frame",
    "aether": "preferred-frame",
    "tetrad": "torsional-geometry",
    "torsion": "torsional-geometry",
    "second_metric": "second-metric",
}

# The property record 0003 refuses that is not a family, named once so that the
# verdict and the documentation cannot use two spellings for it.
SCALAR_FORCE_RANGE: Final = "scalar-force-range-against-the-regime"


@dataclass(frozen=True)
class Reason:
    """One statement behind a verdict, and where in the document it came from.

    `about` is the family, the property or the part of the covered class this
    reason is about. `where` points at the place in the document, and `detail`
    is the sentence a person reads. Issue #28 is where a refusal grows the four
    parts it owes that person, and this is the value those parts are built from.
    """

    about: str
    where: str
    detail: str


@dataclass(frozen=True)
class Verdict:
    """What the gate decided, why, and what it did not look at."""

    state: str
    reasons: tuple[Reason, ...] = field(default=())
    # Properties record 0003 names that this verdict did not decide. An entry
    # here narrows a covered verdict and is reported rather than dropped.
    not_evaluated: tuple[Reason, ...] = field(default=())

    def reaches_the_next_stage(self) -> bool:
        """True for a covered document and for nothing else.

        The one question a later stage asks. Written as a method on the verdict
        rather than as a comparison at each call site, so a stage cannot get it
        wrong by comparing against the wrong constant.
        """
        return self.state == COVERED


def _fields(document: dict[str, object]) -> list[dict[str, object]]:
    declared = document.get("fields")
    if not isinstance(declared, list):
        return []
    return [member for member in declared if isinstance(member, dict)]


def _heads(document: dict[str, object]) -> list[tuple[int, str]]:
    lagrangian = document.get("lagrangian")
    if not isinstance(lagrangian, dict):
        return []
    terms = lagrangian.get("terms")
    if not isinstance(terms, list):
        return []
    found = []
    for index, term in enumerate(terms):
        if isinstance(term, dict) and isinstance(term.get("head"), str):
            found.append((index, str(term["head"])))
    return found


def _refused_reasons(document: dict[str, object]) -> list[Reason]:
    """Every named family this document matches, in the order it is read in."""
    found: list[Reason] = []
    for index, head in _heads(document):
        family = HEAD_FAMILIES.get(head)
        if family is not None:
            found.append(
                Reason(
                    about=family,
                    where=f"lagrangian.terms[{index}].head",
                    detail=(
                        f"the term {head!r} puts this document in the refused "
                        f"family {family!r}, and {FAMILIES[family]}"
                    ),
                )
            )
    for index, member in enumerate(_fields(document)):
        role = member.get("role")
        family = ROLE_FAMILIES.get(role) if isinstance(role, str) else None
        if family is not None:
            found.append(
                Reason(
                    about=family,
                    where=f"fields[{index}].role",
                    detail=(
                        f"a field with the role {role!r} puts this document in "
                        f"the refused family {family!r}, and {FAMILIES[family]}"
                    ),
                )
            )
    metrics = [
        index
        for index, member in enumerate(_fields(document))
        if member.get("role") == "metric"
    ]
    if len(metrics) > 1:
        found.append(
            Reason(
                about="second-metric",
                where=f"fields[{metrics[1]}].role",
                detail=(
                    f"the document declares {len(metrics)} metric fields, and "
                    + FAMILIES["second-metric"]
                ),
            )
        )
    return found


def _unplaceable_reasons(document: dict[str, object]) -> list[Reason]:
    """Every way this document is outside the covered class and matches no family."""
    found: list[Reason] = []
    dimension = document.get("manifold")
    if isinstance(dimension, dict):
        declared = dimension.get("dimension")
        if declared != COVERED_DIMENSION:
            found.append(
                Reason(
                    about="dimension",
                    where="manifold.dimension",
                    detail=(
                        f"the covered class is {COVERED_DIMENSION} dimensional "
                        f"and this document declares {declared!r}, which no "
                        "family record 0003 refuses by name covers either"
                    ),
                )
            )
        signature = dimension.get("signature")
        if signature != COVERED_SIGNATURE:
            found.append(
                Reason(
                    about="signature",
                    where="manifold.signature",
                    detail=(
                        f"record 0008 fixes the signature {COVERED_SIGNATURE} "
                        f"and this document declares {signature!r}, so it is "
                        "not written in the conventions this pipeline reads"
                    ),
                )
            )
    for index, member in enumerate(_fields(document)):
        role = member.get("role")
        if not isinstance(role, str):
            continue
        if role in COVERED_ROLES or role in ROLE_FAMILIES:
            continue
        found.append(
            Reason(
                about="field-role",
                where=f"fields[{index}].role",
                detail=(
                    f"the field role {role!r} is one this gate has no case for, "
                    "so the document is in neither the covered class nor a "
                    "family record 0003 refuses by name"
                ),
            )
        )
    scalars = [
        index
        for index, member in enumerate(_fields(document))
        if member.get("role") == "scalar"
    ]
    if len(scalars) > 1:
        found.append(
            Reason(
                about="field-content",
                where=f"fields[{scalars[1]}].role",
                detail=(
                    "the covered class carries at most one additional scalar "
                    f"field and this document declares {len(scalars)}, which no "
                    "family record 0003 refuses by name covers either"
                ),
            )
        )
    # A head the schema admits that neither map above has a case for. The suite
    # refuses that state in the tree, and this arm is what happens if one
    # arrives anyway: the document is unplaceable rather than covered, so a head
    # added to the schema alone cannot reach the algebra by falling through.
    for index, head in _heads(document):
        if head in COVERED_HEADS or head in HEAD_FAMILIES:
            continue
        found.append(
            Reason(
                about="term-head",
                where=f"lagrangian.terms[{index}].head",
                detail=(
                    f"the term head {head!r} is one this gate has no case for, "
                    "so the document is in neither the covered class nor a "
                    "family record 0003 refuses by name"
                ),
            )
        )
    return found


def _not_evaluated(document: dict[str, object]) -> list[Reason]:
    """The refusals record 0003 names that this gate did not decide.

    One today. It is listed for every document carrying a scalar field, because
    the question is asked of every such document and the answer is the same one:
    not decided here.
    """
    scalars = [
        index
        for index, member in enumerate(_fields(document))
        if member.get("role") == "scalar"
    ]
    if not scalars:
        return []
    return [
        Reason(
            about=SCALAR_FORCE_RANGE,
            where=f"fields[{scalars[0]}]",
            detail=(
                "record 0003 refuses a scalar whose mass puts the range of the "
                "extra force inside the regime the operator is asking about. "
                "That comparison is a mass against a length, which is an "
                "evaluation, and evaluation is below the boundary record 0006 "
                "draws. This gate did not decide it, and this verdict is not "
                "evidence either way about it"
            ),
        )
    ]


def _covered_reasons(document: dict[str, object]) -> list[Reason]:
    """Why this document is inside the covered class, stated rather than assumed."""
    found = [
        Reason(
            about="manifold",
            where="manifold",
            detail=(
                f"a {COVERED_DIMENSION} dimensional manifold with the signature "
                f"{COVERED_SIGNATURE}, which is the covered class of record 0003 "
                "read in the conventions of record 0008"
            ),
        )
    ]
    for index, member in enumerate(_fields(document)):
        role = member.get("role")
        found.append(
            Reason(
                about="field-content",
                where=f"fields[{index}]",
                detail=(
                    f"a field with the role {role!r}, which the covered class carries"
                ),
            )
        )
    for index, head in _heads(document):
        found.append(
            Reason(
                about="lagrangian",
                where=f"lagrangian.terms[{index}].head",
                detail=f"the term {head!r}, which is {COVERED_HEADS[head]}",
            )
        )
    return found


def classify(document: object) -> Verdict:
    """Put one document into exactly one of the three states.

    A refused document and an unplaceable one are both stopped, and they are
    told apart because they are different things to be told. Where a document
    matches a refused family and is also outside the covered class in some other
    way, the family wins, because naming the family is more useful to its author
    than saying the gate could not place it.
    """
    unreadable = schema.refusals(document)
    if unreadable:
        return Verdict(
            state=UNPLACEABLE,
            reasons=tuple(
                Reason(
                    about="not-readable",
                    where=refusal.where,
                    detail=(
                        "the document is not in the shape of the schema, so "
                        "there is nothing here to classify: " + refusal.detail
                    ),
                )
                for refusal in unreadable
            ),
        )
    # Past the schema, so the document is a mapping in the shape the schema
    # admits and every read below finds what it is looking for.
    readable: dict[str, object] = document  # type: ignore[assignment]
    refused = _refused_reasons(readable)
    if refused:
        return Verdict(state=REFUSED, reasons=tuple(refused))
    unplaceable = _unplaceable_reasons(readable)
    if unplaceable:
        return Verdict(state=UNPLACEABLE, reasons=tuple(unplaceable))
    return Verdict(
        state=COVERED,
        reasons=tuple(_covered_reasons(readable)),
        not_evaluated=tuple(_not_evaluated(readable)),
    )
