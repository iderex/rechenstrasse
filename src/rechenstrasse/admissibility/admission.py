"""The one value a stage after the gate takes, and the only route to it.

Issue #26 asks for two things the gate alone cannot give. That every document is
placed in one of three states, which `rechenstrasse.admissibility.gate` does.
And that no stage after the gate can be reached without passing it, which
nothing could hold while the only stage after it took an action: an action is
what the reader builds out of bytes, the gate never sees one, and a caller with
an action in hand can walk straight past the gate without writing anything that
looks like a mistake.

So the stage takes `Admitted` instead. `admit` is the only function here that
returns one, it returns one only where the verdict reaches the next stage, and
it reads and gates in that order rather than leaving the order to a caller.

WHAT THIS IS AND IS NOT. It is the shape of the code rather than a check. A
frozen dataclass in Python can be constructed by anybody who imports it, so this
refuses an accident and not a decision: a caller who builds an `Admitted` around
an action the gate never saw has written down that they are going around the
gate, and that is a different act from calling one function instead of another.
The suite does exactly that in the places it has to reach an arm no document can
reach, and each of those says so where it does it.

Why the record and the action travel together. A covered verdict carries what
the gate did not evaluate, and record 0007 reports that list as assumed rather
than verified. A stage that took the action alone would leave the caller to
carry the verdict beside it, and a list of assumptions carried beside a result
is one that gets dropped.
"""

from dataclasses import dataclass, field

from rechenstrasse import representation
from rechenstrasse.admissibility import gate
from rechenstrasse.document import reader, schema


@dataclass(frozen=True)
class Admitted:
    """An action the gate placed inside the covered class, with that verdict.

    Both halves, because they are one result. `verdict.not_evaluated` is what
    narrows the covered statement, and a stage reporting an equation without it
    is reporting a narrower claim as a wider one.
    """

    action: representation.Action
    verdict: gate.Verdict


@dataclass(frozen=True)
class NotAdmitted:
    """Why a document did not reach the stage after the gate.

    Two different things and they stay apart. `refusals` is the reader's, and
    says the bytes never became an action at all. `verdict` is the gate's, and
    says they did and the theory they describe is outside the covered class or
    could not be placed. Collapsing the two would tell an author with a typing
    mistake that their theory was ruled out.
    """

    refusals: tuple[reader.Refusal, ...] = field(default=())
    verdict: gate.Verdict | None = None


def admit(document_text: str) -> Admitted | NotAdmitted:
    """Read a document, gate it, and hand back the value a later stage takes.

    In that order and never the other way round. The gate reads a document in
    the shape of the schema, so bytes that are not one have nothing to classify,
    and the reader is what says so.

    The second reading of the text is the schema's own and cannot refuse
    anything the first did not, since an action exists only where the schema
    admitted the document. It is here rather than threaded through the reader
    because the gate reads plain data and the reader returns an action, and
    handing the parsed mapping back out of the reader would widen what the
    reader promises for the sake of one caller.
    """
    action, refusals = reader.read(document_text)
    if action is None:
        return NotAdmitted(refusals=refusals)
    loaded, _ = schema.read(document_text)
    verdict = gate.classify(loaded)
    if not verdict.reaches_the_next_stage():
        return NotAdmitted(verdict=verdict)
    return Admitted(action=action, verdict=verdict)
