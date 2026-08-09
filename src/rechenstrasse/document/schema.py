"""The schema an action document is written against, and what it refuses.

Issue #24. Record 0004 fixes the input as plain data serialised as text, read by
a loader that constructs strings, numbers, lists and mappings and nothing else,
and it leaves which plain data syntax sits on disk to this module. That syntax
is JSON.

Why JSON rather than the alternatives, since record 0004 asks the question and
does not answer it. The record wants a family with no execution semantics at
all, rather than one that has them and is asked not to use them. JSON has no
tag, no directive, no anchor and no constructor, so there is nothing in a
document that could name a type even if the loader were wrong; `json` is in the
standard library, so the surface that eats a file somebody else wrote adds no
package to the runtime graph; and a Lagrangian term is a tree with a named head
and named arguments, which nests in JSON without the array-of-tables shapes a
table syntax would need. What is given up is the comment, which is why the
metadata below carries a citation field rather than leaving a reader to write
one beside a term.

What this module holds is the schema and the refusals that come out of reading a
document against it. Turning an accepted document into the internal
representation of record 0005 is issue #25 and is not here. A refusal is
returned as a value rather than raised, because the four parts a refusal carries
and the exit status it leaves behind are issue #28, and a value can be given
those parts later while an exception thrown from here could not.

The refusals, and the failure each one exists against:

  unknown-key
      A key the schema does not admit. Ignoring it is how a term the operator
      wrote never reaches the pipeline while the answer still looks reasonable,
      which record 0004 rules out by name. The key is named in the refusal,
      because the mistake worth catching is a key that differs from a valid one
      by a character and a refusal that does not say which key it means leaves
      the author re-reading the whole document.

  missing-key
      A required key the document does not carry. Named for the same reason.

  wrong-kind
      A value of a plain data kind the schema does not admit at that key, a
      string where a number belongs. Without this the two rules above are a
      spell checker over key names.

  unknown-term-head
      A Lagrangian term whose head the schema has no case for. Record 0004
      places this refusal here and says why it is not handed to an expression
      parser instead: an expression parser is a small interpreter, and a term it
      silently reads as something other than what the author meant is the
      failure this board exists to remove.

  unknown-schema-version
      A document written against a version this build does not read. A document
      declares its version so that an old one stays readable after the schema
      has moved, and that only means something if a version nobody here knows is
      refused rather than guessed at.

  not-a-document
      Bytes that are not readable as JSON at all, or that are readable as
      something other than a mapping. This is the one refusal that comes from
      the loader rather than from the schema.

What this module does not decide. Whether the theory a well-formed document
describes is one this pipeline will answer for is the admissibility gate of
issue #26, and record 0003 is where that boundary is drawn. A document can be in
perfect shape here and be refused there, and the two refusals are about
different things.
"""

import json
from dataclasses import dataclass
from typing import Final

# The schema version this build is written against, and the versions it reads. A
# document declares which one it was written for, and record 0004 fixes the
# route a new one arrives by: an issue naming the term, a schema version
# carrying it with a fixture document that uses it, and the matching case in the
# gate of issue #26, so the accepted surface and the refused surface move in one
# change.
CURRENT_SCHEMA_VERSION: Final = 1
READABLE_SCHEMA_VERSIONS: Final = (1,)

# The heads a Lagrangian term may carry, and what each one stands for. A head
# that is not here is refused rather than guessed at.
#
# The set is wider than the covered class of record 0003, and deliberately so.
# Every family that record names as refused is refused for a reason, and a
# reason can only be given to somebody whose document got far enough to be
# classified. A head that is expressible here and refused by the gate of issue
# #26 tells its author which family they are in and why; a head this schema had
# never heard of would tell them they had made a typing mistake. Which heads
# belong to which family is the gate's to say and is not written here, and the
# suite in `tests/rechenstrasse/test_admissibility.py` refuses a head this
# schema admits that the gate has no case for, so the accepted surface and the
# refused surface cannot move apart.
#
# There is exactly one way to write each covered term, which is a property the
# canonical form of record 0005 rests on. `ricci_scalar` carries a constant
# coefficient and `horndeski_g4` carries a function of the field alone, so a
# theory whose coefficient on the curvature scalar does not move is written the
# first way and one whose coefficient does move is written the second, and no
# theory has a choice about which.
TERM_HEADS: Final[dict[str, str]] = {
    "ricci_scalar": (
        "a constant coefficient times the curvature scalar, which is the "
        "Einstein-Hilbert term"
    ),
    "cosmological_constant": (
        "the constant term carried on the geometry side, with the symbol record "
        "0008 fixes for it"
    ),
    "horndeski_g2": "G2(phi, X), which is where a potential enters",
    "horndeski_g3": "-G3(phi, X) box phi, with the sign record 0008 fixes",
    "horndeski_g4": "G4(phi) R, with G4 a function of the field alone",
    "horndeski_g4_kinetic": "G4(phi, X) R, the same term with kinetic dependence",
    "horndeski_g5": "the G5 sector, in any of the forms it is written in",
    "torsion_scalar": "the torsion scalar T, and any function of it",
    "gauss_bonnet": "the Gauss-Bonnet combination",
    "ricci_squared": "the square of the Ricci tensor, contracted on both indices",
    "riemann_squared": "the square of the Riemann tensor, contracted on all four",
}


@dataclass(frozen=True)
class Key:
    """One key of one mapping in the document, and what may sit under it.

    `kinds` are the plain data kinds the loader can produce that this key
    admits. `mapping` is the schema of the mapping under the key, where the
    value is one. `element` and `element_kinds` are the same two things for the
    members of a list, and a key uses at most one of them.
    """

    name: str
    required: bool
    kinds: tuple[type, ...]
    mapping: tuple["Key", ...] = ()
    element: tuple["Key", ...] = ()
    element_kinds: tuple[type, ...] = ()


# A number in a document is an integer or a fraction, and never a boolean.
# `bool` is a subclass of `int` in this language, so a document writing `true`
# where a count belongs would otherwise pass, and the check below is what keeps
# the two apart.
NUMBER: Final[tuple[type, ...]] = (int, float)

# The schema itself. One document describes one theory, and every section issue
# #24 names is required, because a document that leaves one out is a document
# whose author has not said what they meant rather than one that meant the
# default.
DOCUMENT: Final[tuple[Key, ...]] = (
    Key("schema_version", required=True, kinds=(int,)),
    Key(
        "metadata",
        required=True,
        kinds=(dict,),
        mapping=(
            # What a result cites when it names its input. The identifier is
            # what a run record and a parity row refer to, and the citation is
            # what a reader follows back to the paper the theory came from.
            Key("identifier", required=True, kinds=(str,)),
            Key("name", required=True, kinds=(str,)),
            Key("citation", required=True, kinds=(str,)),
        ),
    ),
    Key(
        "manifold",
        required=True,
        kinds=(dict,),
        mapping=(
            Key("dimension", required=True, kinds=(int,)),
            # Written out rather than assumed, so a document that meant another
            # one says so here and is refused by the gate of issue #26 instead
            # of being read in conventions it was not written in.
            Key("signature", required=True, kinds=(str,)),
        ),
    ),
    Key(
        "fields",
        required=True,
        kinds=(list,),
        element=(
            Key("symbol", required=True, kinds=(str,)),
            Key("role", required=True, kinds=(str,)),
            # The symmetries belong to the field rather than to the term that
            # mentions it, which is record 0005's rule and the reason two terms
            # naming one tensor cannot disagree about how it behaves under an
            # index swap.
            Key("symmetries", required=True, kinds=(list,), element_kinds=(str,)),
        ),
    ),
    Key(
        "lagrangian",
        required=True,
        kinds=(dict,),
        mapping=(
            Key(
                "terms",
                required=True,
                kinds=(list,),
                element=(
                    Key("head", required=True, kinds=(str,)),
                    # The symbol standing in front of the term, carried as a
                    # name rather than as a number, because the pipeline derives
                    # expressions and an operator who wrote a number here would
                    # get it back in the answer with nothing to vary.
                    Key("coefficient", required=True, kinds=(str,)),
                ),
            ),
        ),
    ),
    Key(
        "matter",
        required=True,
        kinds=(dict,),
        mapping=(
            Key("coupling", required=True, kinds=(str,)),
            Key("frame", required=True, kinds=(str,)),
        ),
    ),
    Key(
        "parameters",
        required=True,
        kinds=(list,),
        element=(
            Key("symbol", required=True, kinds=(str,)),
            # The range the author claims, and null on a side that is open. An
            # absent bound and an unbounded one are different statements, so
            # both keys are required and the open side is written rather than
            # left out.
            Key("minimum", required=True, kinds=(*NUMBER, type(None))),
            Key("maximum", required=True, kinds=(*NUMBER, type(None))),
            Key("claimed_by", required=True, kinds=(str,)),
        ),
    ),
    # The regime the operator is asking about. Record 0003 refuses a scalar
    # whose mass puts the range of the extra force inside that regime, and that
    # is a property of the input rather than of a family, so the gate of issue
    # #26 needs it as part of the document rather than as a flag on a command
    # line.
    Key(
        "regime",
        required=True,
        kinds=(dict,),
        mapping=(
            Key("name", required=True, kinds=(str,)),
            Key("length_scale", required=True, kinds=(str,)),
        ),
    ),
)


@dataclass(frozen=True)
class Refusal:
    """One reason a document was not accepted, and where in it that reason sits.

    `rule` is one of the identifiers this module's docstring lists. `where` is
    the path to the offending place, written the way a reader would point at it,
    and `named` is the key, the head or the version the refusal is about, so
    that the thing being refused is a field rather than something to be read
    back out of a sentence. `detail` is that sentence, and issue #28 is where a
    refusal grows the four parts it owes a person who hit one.
    """

    rule: str
    where: str
    named: str
    detail: str


def _kind_name(kind: type) -> str:
    return "null" if kind is type(None) else kind.__name__


def _kind_of(value: object) -> str:
    if value is None:
        return "null"
    return type(value).__name__


def _admits(value: object, kinds: tuple[type, ...]) -> bool:
    # A boolean is an integer here unless it is said not to be, and a document
    # writing `true` where a dimension belongs is the case that matters.
    if isinstance(value, bool) and bool not in kinds:
        return False
    return isinstance(value, kinds)


def _join(where: str, name: str) -> str:
    return name if where == "" else f"{where}.{name}"


def _check_mapping(value: object, keys: tuple[Key, ...], where: str) -> list[Refusal]:
    """Read one mapping against the keys the schema admits at that place."""
    found: list[Refusal] = []
    if not isinstance(value, dict):
        return found
    admitted = {key.name: key for key in keys}
    for name in value:
        if name not in admitted:
            found.append(
                Refusal(
                    rule="unknown-key",
                    where=_join(where, str(name)),
                    named=str(name),
                    detail=(
                        f"the key {name!r} is not one this schema admits at "
                        f"{where or 'the top level'}, and the keys it admits "
                        f"there are {', '.join(sorted(admitted))}"
                    ),
                )
            )
    for key in keys:
        if key.name not in value:
            if key.required:
                found.append(
                    Refusal(
                        rule="missing-key",
                        where=_join(where, key.name),
                        named=key.name,
                        detail=(
                            f"the key {key.name!r} is required at "
                            f"{where or 'the top level'} and the document does "
                            "not carry it"
                        ),
                    )
                )
            continue
        found.extend(_check_value(value[key.name], key, _join(where, key.name)))
    return found


def _check_value(value: object, key: Key, where: str) -> list[Refusal]:
    """Read one value against the one key that admits it."""
    if not _admits(value, key.kinds):
        return [
            Refusal(
                rule="wrong-kind",
                where=where,
                named=key.name,
                detail=(
                    f"the value at {where} is {_kind_of(value)} and this schema "
                    "admits "
                    + " or ".join(_kind_name(kind) for kind in key.kinds)
                    + " there"
                ),
            )
        ]
    if key.mapping:
        return _check_mapping(value, key.mapping, where)
    if isinstance(value, list):
        return _check_list(value, key, where)
    return []


def _check_list(value: list[object], key: Key, where: str) -> list[Refusal]:
    found: list[Refusal] = []
    for index, member in enumerate(value):
        at = f"{where}[{index}]"
        if key.element:
            if not isinstance(member, dict):
                found.append(
                    Refusal(
                        rule="wrong-kind",
                        where=at,
                        named=key.name,
                        detail=(
                            f"the member at {at} is {_kind_of(member)} and this "
                            "schema admits a mapping there"
                        ),
                    )
                )
                continue
            found.extend(_check_mapping(member, key.element, at))
        elif key.element_kinds and not _admits(member, key.element_kinds):
            found.append(
                Refusal(
                    rule="wrong-kind",
                    where=at,
                    named=key.name,
                    detail=(
                        f"the member at {at} is {_kind_of(member)} and this "
                        "schema admits "
                        + " or ".join(_kind_name(kind) for kind in key.element_kinds)
                        + " there"
                    ),
                )
            )
    return found


def _check_version(document: dict[str, object]) -> list[Refusal]:
    declared = document.get("schema_version")
    if not isinstance(declared, int) or isinstance(declared, bool):
        return []
    if declared in READABLE_SCHEMA_VERSIONS:
        return []
    readable = ", ".join(str(version) for version in READABLE_SCHEMA_VERSIONS)
    return [
        Refusal(
            rule="unknown-schema-version",
            where="schema_version",
            named=str(declared),
            detail=(
                f"the document declares schema version {declared} and this "
                f"build reads {readable}"
            ),
        )
    ]


def _check_term_heads(document: dict[str, object]) -> list[Refusal]:
    lagrangian = document.get("lagrangian")
    if not isinstance(lagrangian, dict):
        return []
    terms = lagrangian.get("terms")
    if not isinstance(terms, list):
        return []
    found: list[Refusal] = []
    for index, term in enumerate(terms):
        if not isinstance(term, dict):
            continue
        head = term.get("head")
        if not isinstance(head, str) or head in TERM_HEADS:
            continue
        found.append(
            Refusal(
                rule="unknown-term-head",
                where=f"lagrangian.terms[{index}].head",
                named=head,
                detail=(
                    f"the term head {head!r} is not one this schema has a case "
                    "for, and the heads it has cases for are "
                    + ", ".join(sorted(TERM_HEADS))
                ),
            )
        )
    return found


def refusals(document: object) -> tuple[Refusal, ...]:
    """Every reason this document is not in the shape the schema admits.

    An empty result says the document is readable, and it says nothing about
    whether the theory it describes is one this pipeline will answer for. That
    is the gate of issue #26.

    Every reason rather than the first one, because an author fixing a document
    a key at a time learns about the next mistake only after another run, and
    the mistakes here are the kind that come in groups.
    """
    if not isinstance(document, dict):
        return (
            Refusal(
                rule="not-a-document",
                where="",
                named=_kind_of(document),
                detail=(
                    f"the document reads as {_kind_of(document)} and one action "
                    "document is a mapping"
                ),
            ),
        )
    found = _check_mapping(document, DOCUMENT, "")
    found.extend(_check_version(document))
    found.extend(_check_term_heads(document))
    return tuple(found)


def read(text: str) -> tuple[object | None, tuple[Refusal, ...]]:
    """Turn the bytes of a document into plain data, or say why they are not one.

    The loader constructs strings, numbers, lists and mappings and nothing else,
    which is record 0004's condition on the input and the reason a document from
    a stranger is data rather than a program. Nothing here evaluates a string
    from the document as an expression.
    """
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as malformed:
        return None, (
            Refusal(
                rule="not-a-document",
                where=f"line {malformed.lineno}, column {malformed.colno}",
                named=malformed.msg,
                detail=(
                    "the bytes are not readable as a document: "
                    f"{malformed.msg} at line {malformed.lineno}, column "
                    f"{malformed.colno}"
                ),
            ),
        )
    return loaded, refusals(loaded)
