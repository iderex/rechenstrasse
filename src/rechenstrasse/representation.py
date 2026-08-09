"""The internal representation of record 0005, in one place.

What the stages pass to each other. Record 0005 fixes two things about it that
this module is built to hold rather than to describe: a tensor is declared once
and every mention of it resolves to that declaration, and the symmetries belong
to the tensor rather than to the term that mentions it. Both exist against the
same failure, an expression carrying two contradictory statements about one
object, which surfaces later as a canonical form that is not canonical.

Everything here is a frozen value. Two actions read from the same bytes compare
equal, which is what lets the round trip in issue #25 be an equality rather than
a walk over fields, and nothing above this module can edit a declaration out
from under a term that resolved to it.

What is not here, said plainly rather than left to be discovered. Record 0005
describes the representation as an expression over tensor terms with abstract
indices, and there is no index type below. The document format of record 0004
carries no index: a Lagrangian is a scalar, its terms are written as a named
head with a coefficient, and every index inside a head is contracted by the
definition of that head. So a reader of a document produces no free index, and
an index type introduced here today would be a type with no user and no test
that could fail. It arrives with the stage that first writes a term carrying a
free index, which is the metric variation of issue #30, and the tensor
declarations below are what it will attach to.

The seam of record 0005 is not here either. Canonicalisation takes an expression
and returns its canonical form, and this module holds no comparison beyond the
equality the language gives a frozen value, which is equality of structure and
not of meaning. Two documents that describe the same theory in different words
are two different actions here, and telling them apart is the seam's work in
issue #33.
"""

from dataclasses import dataclass
from typing import Final

# The roles a field may carry, and how many index slots a field in that role
# has. The count is what makes a symmetry declaration refusable: a swap of two
# slots is not a statement anybody can make about a field that has fewer than
# two, and record 0005 puts the symmetries on the tensor precisely so that such
# a statement is judged once, where the field is declared.
#
# The set is wider than the covered class of record 0003 for the same reason the
# schema's set of heads is: a document from a refused family reaches the gate
# and is told which family it is in, and it can only be told that if it could be
# read first.
SLOTS: Final[dict[str, int]] = {
    "metric": 2,
    "scalar": 0,
    "vector": 1,
    "aether": 1,
    "tetrad": 2,
    "torsion": 3,
    "second_metric": 2,
}

# The symmetries a declaration may carry, and the smallest number of slots each
# one is a statement about. A symmetry that is not here is refused rather than
# carried through to a canonicaliser that would have to guess what it meant.
SYMMETRIES: Final[dict[str, int]] = {
    "symmetric": 2,
    "antisymmetric": 2,
}


@dataclass(frozen=True)
class Tensor:
    """One field, declared once, with the symmetries that belong to it.

    `slots` is the number of index positions the field has, from its role, and
    it is carried here rather than looked up at each use so that a term holding
    a declaration holds everything it needs to know about the object.
    """

    symbol: str
    role: str
    slots: int
    symmetries: tuple[str, ...]


@dataclass(frozen=True)
class Term:
    """One term of a Lagrangian: a coefficient, a head, and what it is built from.

    `mentions` are the declarations this term resolved to, in the order the
    head's requirements are written. They are the declaration objects rather
    than the symbols, which is the whole of what "resolved" means here: a term
    cannot be holding a symmetry the field's declaration does not carry, because
    it is not holding a copy of anything.
    """

    head: str
    coefficient: str
    mentions: tuple[Tensor, ...]


@dataclass(frozen=True)
class Lagrangian:
    """The terms, in the order the document wrote them.

    The order is kept rather than sorted. Reordering is canonicalisation, which
    sits behind the seam of record 0005, and a reader that quietly sorted would
    be doing that work in the one place issue #25 says it must not.
    """

    terms: tuple[Term, ...]


@dataclass(frozen=True)
class Manifold:
    dimension: int
    signature: str


@dataclass(frozen=True)
class Metadata:
    identifier: str
    name: str
    citation: str


@dataclass(frozen=True)
class Matter:
    coupling: str
    frame: str


@dataclass(frozen=True)
class Parameter:
    """A symbol the theory carries, and the range its author claims for it.

    An absent bound is `None` and is a different statement from a bound of zero,
    which is why the document requires both keys and this carries both.
    """

    symbol: str
    minimum: int | float | None
    maximum: int | float | None
    claimed_by: str


@dataclass(frozen=True)
class Regime:
    """What the operator is asking about, which record 0003's last refusal reads."""

    name: str
    length_scale: str


@dataclass(frozen=True)
class Action:
    """One theory, in the form the stages after the reader work on."""

    schema_version: int
    metadata: Metadata
    manifold: Manifold
    fields: tuple[Tensor, ...]
    lagrangian: Lagrangian
    matter: Matter
    parameters: tuple[Parameter, ...]
    regime: Regime

    def declaration(self, symbol: str) -> Tensor | None:
        """The one declaration for a symbol, or nothing where there is none.

        One declaration and never a list, because a document carrying two for
        one symbol is refused by the reader before an action exists.
        """
        for declared in self.fields:
            if declared.symbol == symbol:
                return declared
        return None
