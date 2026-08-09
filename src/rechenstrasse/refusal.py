"""What a refusal says to the person who hit it, and what it says to a machine.

Issue #28. This is the surface most users of this pipeline meet first, because
the interesting theories are the ones near the edge, and a refusal that says
`unsupported` sends its author away with nothing to do next.

Every refusal carries four parts.

  what
      The family or the property that fired, named. Not a category, the thing
      itself.

  breaks
      Which assumption of this pipeline the input breaks. This is the part that
      turns a rule into an explanation, because an author who knows which
      assumption they are outside can tell whether they are outside it on
      purpose.

  needs
      What would have to exist for the answer to be computable. Sometimes that
      is work nobody has done, sometimes it is a decision nobody has taken, and
      sometimes it is a correction to the document that takes one line. Those
      are very different situations to be in and the refusal says which.

  record
      The decision record that drew the line, as a path in this tree. The
      argument lives there and is not restated here, so the two cannot drift.

It is machine readable as well as readable, because a parity run and any
downstream automation have to tell a refusal from a crash without parsing
English. `as_data` is that form, and the exit statuses below are the other half:
a refusal leaves a status of its own, distinct from success and from an internal
error.

Where the parts come from. The schema in `rechenstrasse.document.schema` and the
gate in `rechenstrasse.admissibility.gate` each produce their own refusals, in
their own vocabulary, and neither of them knows what an author should do next.
The tables here are what add that, one entry per rule and per family, and the
suite refuses a rule or a family with no entry, so a refusal nobody wrote a
`needs` for cannot reach a person as a bare identifier.

What this module does not do. Nothing here exits a process. The exit statuses
are constants and a mapping from a set of refusals onto one of them; the command
that would return one to a shell is issue #59 and does not exist yet, so no test
in this tree asserts the status a real run left behind. That is stated rather
than worked around, and it is the half of this issue's done-when that is open.
"""

from dataclasses import dataclass
from typing import Final

from rechenstrasse.admissibility import gate
from rechenstrasse.document import schema

# The three statuses. Success is the shell's own convention. A refusal is its
# own number rather than the general failure status, because "this pipeline will
# not answer for your input" and "this pipeline broke" are the two things a
# parity run has to tell apart without reading a message. The internal error
# takes the number reserved for a program that failed at its own job, so the
# refusal number is the one that is unusual and the crash is where a reader
# expects to find it.
EXIT_SUCCESS: Final = 0
EXIT_REFUSED: Final = 3
EXIT_INTERNAL_ERROR: Final = 70

_RECORD_0003: Final = "docs/decisions/0003-covered-theories-and-refused-families.md"
_RECORD_0004: Final = "docs/decisions/0004-an-action-is-a-document.md"
_RECORD_0006: Final = "docs/decisions/0006-where-exact-algebra-ends.md"
_RECORD_0008: Final = "docs/decisions/0008-sign-index-and-unit-conventions.md"


@dataclass(frozen=True)
class Grounds:
    """The three parts a refusal cannot work out for itself."""

    breaks: str
    needs: str
    record: str


# One entry per rule the schema refuses by. A document in the wrong shape is a
# document the author can repair, and every `needs` here says which line.
SCHEMA_GROUNDS: Final[dict[str, Grounds]] = {
    "unknown-key": Grounds(
        breaks=(
            "the input is data with a fixed set of keys, and an unrecognised "
            "one is refused rather than ignored, because a silently dropped "
            "term is the failure where the operator writes a term, the "
            "pipeline never sees it, and the answer looks reasonable"
        ),
        needs=(
            "the key removed or corrected, or, where it carries a term nobody "
            "can express today, an issue naming the term and a schema version "
            "carrying it with the matching case in the gate"
        ),
        record=_RECORD_0004,
    ),
    "missing-key": Grounds(
        breaks=(
            "every part of a document is required, because a document that "
            "leaves one out is one whose author has not said what they meant "
            "rather than one that meant the default"
        ),
        needs="the key written into the document, with the value the author meant",
        record=_RECORD_0004,
    ),
    "wrong-kind": Grounds(
        breaks=(
            "a value is read as the plain data kind the schema admits there, "
            "and never converted into it, because a conversion is a guess at "
            "what the author meant"
        ),
        needs="the value written as the kind the schema admits at that place",
        record=_RECORD_0004,
    ),
    "unknown-term-head": Grounds(
        breaks=(
            "a term is a structure with a head this pipeline has a case for, "
            "and a head it does not have a case for is refused rather than "
            "handed to an expression parser to see what happens"
        ),
        needs=(
            "the head corrected, or an issue naming the term and the theory it "
            "comes from, a schema version carrying it, and the matching case "
            "in the admissibility gate, so the accepted surface and the "
            "refused surface move in one change"
        ),
        record=_RECORD_0004,
    ),
    "unknown-schema-version": Grounds(
        breaks=(
            "a document declares the schema version it was written against, "
            "which is what makes an old document readable after the schema has "
            "moved, and a version this build does not know is refused rather "
            "than guessed at"
        ),
        needs=(
            "a build of this pipeline that reads that version, or the document "
            "rewritten against a version this one reads"
        ),
        record=_RECORD_0004,
    ),
    "not-a-document": Grounds(
        breaks=(
            "the input is plain data serialised as text and is never executed, "
            "so bytes that do not read as one mapping are not an action"
        ),
        needs="the file written as a single JSON mapping",
        record=_RECORD_0004,
    ),
}

# One entry per family the gate refuses by name, and per way it can fail to
# place a document. The `needs` for a family is deliberately not encouraging:
# these are boundaries with reasons behind them, and a refusal that suggested a
# flag would be inviting somebody to work around the argument.
GATE_GROUNDS: Final[dict[str, Grounds]] = {
    "derivative-coupling": Grounds(
        breaks=(
            "the post-Newtonian reading this pipeline performs is what an "
            "experiment measures only outside the regime derivative couplings "
            "put a theory in"
        ),
        needs=(
            "a post-Newtonian treatment of this sector in the literature that "
            "this pipeline could reproduce, which is one of the two conditions "
            "record 0003 names for reopening its boundary"
        ),
        record=_RECORD_0003,
    ),
    "torsional-geometry": Grounds(
        breaks=(
            "every variational step in this pipeline assumes the Levi-Civita "
            "connection of the metric"
        ),
        needs=(
            "a variational stage written for a torsional connection, which is "
            "a different pipeline rather than a case in this one"
        ),
        record=_RECORD_0003,
    ),
    "preferred-frame": Grounds(
        breaks=(
            "this version solves for two post-Newtonian parameters, and a "
            "preferred frame brings in ones it does not solve for"
        ),
        needs=(
            "the preferred-frame parameters derived rather than inherited, "
            "which is the work issue #40 keeps separate from a reported zero"
        ),
        record=_RECORD_0003,
    ),
    "second-metric": Grounds(
        breaks="the internal representation carries one metric",
        needs=(
            "a representation with a second metric in it, and a record "
            "superseding the one that fixed the first"
        ),
        record=_RECORD_0003,
    ),
    "quadratic-curvature": Grounds(
        breaks=(
            "the standard post-Newtonian metric ansatz is the right shape of "
            "solution only where there are no extra propagating modes"
        ),
        needs=(
            "an ansatz that carries the extra modes, and a reason to believe "
            "the comparison against the published corpus still means the same "
            "thing"
        ),
        record=_RECORD_0003,
    ),
    "dimension": Grounds(
        breaks="the covered class is four dimensional",
        needs=(
            "the document corrected where the dimension was a mistake, and "
            "otherwise a covered class that reaches other dimensions, which no "
            "record draws"
        ),
        record=_RECORD_0003,
    ),
    "signature": Grounds(
        breaks=(
            "every stage reads and writes in one set of sign, index and unit "
            "conventions, and a document in another set is not translated in "
            "anybody's head"
        ),
        needs=(
            "the document rewritten in the conventions this pipeline reads, "
            "with the translation recorded beside any value quoted from a "
            "source that used another set"
        ),
        record=_RECORD_0008,
    ),
    "field-role": Grounds(
        breaks=(
            "the covered class is built from the metric, its curvature and at "
            "most one additional scalar field, and a role outside that is "
            "neither covered nor a family record 0003 refuses by name"
        ),
        needs=(
            "the role corrected where it was a mistake, and otherwise an "
            "argument about whether that field content belongs in the covered "
            "class at all"
        ),
        record=_RECORD_0003,
    ),
    "field-content": Grounds(
        breaks="the covered class carries at most one additional scalar field",
        needs=(
            "a covered class that reaches more than one extra field, which "
            "would be a record superseding the one that drew this boundary"
        ),
        record=_RECORD_0003,
    ),
    "term-head": Grounds(
        breaks=(
            "a term the schema admits has a matching case in the gate, so that "
            "the accepted surface and the refused surface move together"
        ),
        needs=(
            "the missing case in the gate, in the change that added the head "
            "to the schema"
        ),
        record=_RECORD_0004,
    ),
    "not-readable": Grounds(
        breaks=(
            "the gate classifies a document it can read, and a document that "
            "is not in the shape of the schema is not one"
        ),
        needs="the document repaired against the schema, and read again",
        record=_RECORD_0004,
    ),
    gate.SCALAR_FORCE_RANGE: Grounds(
        breaks=(
            "record 0003 refuses a scalar whose mass puts the range of the "
            "extra force inside the regime the operator is asking about, and "
            "deciding that compares a mass against a length"
        ),
        needs=(
            "an evaluation stage, which is below the boundary record 0006 "
            "draws and has no machinery in this tree"
        ),
        record=_RECORD_0006,
    ),
}


@dataclass(frozen=True)
class Refusal:
    """One refusal, in the four parts a person who hit it needs.

    `where` is not one of the four. It is the place in the document, kept
    because an author with a long document needs to find the term as well as
    understand it.
    """

    what: str
    where: str
    breaks: str
    needs: str
    record: str

    def as_data(self) -> dict[str, str]:
        """The machine readable form.

        Flat strings rather than nested structure, so that a parity run reading
        this does not have to know the shape of a document to report it.
        """
        return {
            "what": self.what,
            "where": self.where,
            "breaks": self.breaks,
            "needs": self.needs,
            "record": self.record,
        }

    def as_text(self) -> str:
        """The readable form, in the order a person asks the questions in."""
        return (
            f"Refused: {self.what}, at {self.where or 'the document'}.\n"
            f"What this breaks: {self.breaks}.\n"
            f"What would have to exist: {self.needs}.\n"
            f"Where the line was drawn: {self.record}."
        )


def from_schema(refusal: schema.Refusal) -> Refusal:
    """Give a schema refusal the three parts the schema cannot know."""
    grounds = SCHEMA_GROUNDS[refusal.rule]
    return Refusal(
        what=f"{refusal.rule}: {refusal.detail}",
        where=refusal.where,
        breaks=grounds.breaks,
        needs=grounds.needs,
        record=grounds.record,
    )


def from_verdict(verdict: gate.Verdict) -> tuple[Refusal, ...]:
    """Every refusal behind a verdict that is not covered.

    A covered verdict has no refusals and returns none, which is not the same
    thing as a verdict with nothing to say: what a covered verdict did not
    decide is `not_evaluated` and is reported by `undecided` below.
    """
    if verdict.reaches_the_next_stage():
        return ()
    return tuple(from_reason(reason) for reason in verdict.reasons)


def undecided(verdict: gate.Verdict) -> tuple[Refusal, ...]:
    """What the verdict did not decide, in the same four parts.

    The same shape as a refusal on purpose. A property that was not evaluated
    and a property that fired are both things an operator has to know about, and
    a reader who has learned to read one can read the other. What keeps them
    apart is that these are reported beside a result rather than instead of one,
    and record 0007's provenance block is where they go.
    """
    return tuple(from_reason(reason) for reason in verdict.not_evaluated)


def from_reason(reason: gate.Reason) -> Refusal:
    grounds = GATE_GROUNDS[reason.about]
    return Refusal(
        what=f"{reason.about}: {reason.detail}",
        where=reason.where,
        breaks=grounds.breaks,
        needs=grounds.needs,
        record=grounds.record,
    )


def status_for(refusals: tuple[Refusal, ...]) -> int:
    """The status a run leaves behind, given what it refused.

    Two of the three statuses are decided here. The third is not: an internal
    error is a defect in this pipeline rather than a property of the input, so
    nothing derives it from a document, and whatever catches one is what returns
    it.
    """
    return EXIT_REFUSED if refusals else EXIT_SUCCESS
