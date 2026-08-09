"""The reader that turns an accepted document into the internal representation.

Issue #25, over the representation record 0005 fixes. It reads a document the
schema admits and produces the action the later stages work on, and it does
nothing else: no simplification, no canonicalisation, no reordering of terms.
Those are stages with their own tests, and a failure that could have come from
any of them is a failure nobody can place.

What this refuses that nothing before it does. The schema decides the shape of
the bytes and the gate decides which class the theory is in, and a document can
pass both while saying two things about one object. Record 0005 puts the
symmetries on the tensor rather than on the term precisely so that such a
document is refused where the field is declared, and this is that place:

  symbol-declared-twice
      Two declarations under one symbol, counting the fields and the parameters
      together because they name objects in one expression. This is the failure
      record 0005 names: a later stage resolving a mention would be choosing
      between two declarations, and whichever it chose, the expression would
      carry a statement the document contradicts somewhere else.

  unknown-role
      A field role that has no number of index slots written for it. A
      declaration cannot be built without that number, and a role whose slot
      count is a guess is a symmetry nobody can judge.

  unknown-symmetry
      A symmetry this representation has no case for. Carrying it through would
      hand a canonicaliser a word whose meaning it would have to guess, which is
      the same failure as an executed input one level down.

  symmetry-without-slots
      A symmetry on a field with too few index slots for it to be a statement
      about anything. A scalar declared symmetric is not a scalar with an extra
      property, it is an author who meant something else.

  undeclared-field
      A term whose head is built from a field the document does not declare. The
      schema admits the term and the gate places the theory, and neither asks
      whether the objects the term is about exist.

  ambiguous-field
      Two declarations that could each satisfy one requirement of one head. A
      mention has to resolve to one declaration, and picking either is the
      choice record 0005 exists to remove.

  unresolved-head
      A head the schema admits that this reader has nothing written for. It
      cannot happen in this tree, because the suite holds the two sets against
      each other, and it is refused here anyway: a head that fell through would
      reach the algebra as a term built from nothing.

Every refusal carries a line and a column as well as a path. That is issue #25's
own reason and it is why `positions.py` is in this package: a message naming
`lagrangian.terms[7].head` and no line sends its reader back to counting braces.

A refusal is returned rather than raised, which is the shape the schema uses and
for the same reason. The four parts a refusal owes the person who hit one, and
the exit status behind it, are issue #28, and a value can be given those parts
later.
"""

import json
from dataclasses import dataclass
from typing import Final

from rechenstrasse import representation
from rechenstrasse.document import positions, schema

# Which fields each term head is built from. One entry per requirement, and a
# requirement is the set of roles that can satisfy it, because a torsional term
# is written against whichever of the two torsional roles the document declared.
#
# The suite holds this against the schema's heads in both directions. A head the
# schema admits and this has no entry for would be a term reaching the
# representation with nothing resolved, and an entry here for a head no document
# can carry is a requirement nothing ever reads.
HEAD_NEEDS: Final[dict[str, tuple[frozenset[str], ...]]] = {
    "ricci_scalar": (frozenset({"metric"}),),
    "cosmological_constant": (frozenset({"metric"}),),
    "horndeski_g2": (frozenset({"metric"}), frozenset({"scalar"})),
    "horndeski_g3": (frozenset({"metric"}), frozenset({"scalar"})),
    "horndeski_g4": (frozenset({"metric"}), frozenset({"scalar"})),
    "horndeski_g4_kinetic": (frozenset({"metric"}), frozenset({"scalar"})),
    "horndeski_g5": (frozenset({"metric"}), frozenset({"scalar"})),
    "torsion_scalar": (frozenset({"tetrad", "torsion"}),),
    "gauss_bonnet": (frozenset({"metric"}),),
    "ricci_squared": (frozenset({"metric"}),),
    "riemann_squared": (frozenset({"metric"}),),
}


@dataclass(frozen=True)
class Refusal:
    """One reason this document did not become an action, and where it sits.

    `rule` is one of the identifiers above, or the schema's own where the
    document never got past it, so a caller reads one vocabulary. `where` is the
    path, `at` is the line and column that path resolves to, and `named` is the
    symbol, the role or the key the refusal is about, so the thing refused is a
    field rather than something to be read back out of a sentence.
    """

    rule: str
    where: str
    at: positions.Position
    named: str
    detail: str

    def __str__(self) -> str:
        place = f"{self.at}" if self.where == "" else f"{self.at}, at {self.where}"
        return f"{place}: {self.detail}"


def mapping(holder: dict[str, object], key: str) -> dict[str, object]:
    """The mapping under a key, or an empty one where the document has no mapping.

    The empty result is what a document the schema refused would produce, and
    nothing here is called on one. It exists so that this module reads a
    document without an assertion on every line, and it is exercised directly
    rather than left as a branch nothing takes.
    """
    value = holder.get(key)
    return value if isinstance(value, dict) else {}


def listing(holder: dict[str, object], key: str) -> list[dict[str, object]]:
    """The mappings in the list under a key, and nothing else that list holds."""
    value = holder.get(key)
    if not isinstance(value, list):
        return []
    return [member for member in value if isinstance(member, dict)]


def text(holder: dict[str, object], key: str) -> str:
    """The string under a key, or the empty string where there is not one."""
    value = holder.get(key)
    return value if isinstance(value, str) else ""


def count(holder: dict[str, object], key: str) -> int:
    """The integer under a key, and never a boolean, which is one in this language."""
    value = holder.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def bound(holder: dict[str, object], key: str) -> int | float | None:
    """One end of a claimed range, where an absent bound is written and not left out."""
    value = holder.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return value


def symmetries(member: dict[str, object]) -> tuple[str, ...]:
    """The symmetries one declaration carries, in the order it wrote them."""
    value = member.get("symmetries")
    if not isinstance(value, list):
        return ()
    return tuple(name for name in value if isinstance(name, str))


def _terms(document: dict[str, object]) -> list[dict[str, object]]:
    return listing(mapping(document, "lagrangian"), "terms")


def _symbol_refusals(
    document: dict[str, object], index: dict[str, positions.Position]
) -> list[Refusal]:
    """One symbol names one thing, across the fields and the parameters together."""
    found: list[Refusal] = []
    seen: dict[str, str] = {}
    for key in ("fields", "parameters"):
        for number, member in enumerate(listing(document, key)):
            symbol = text(member, "symbol")
            where = f"{key}[{number}].symbol"
            if symbol in seen:
                found.append(
                    Refusal(
                        rule="symbol-declared-twice",
                        where=where,
                        at=positions.nearest(index, where),
                        named=symbol,
                        detail=(
                            f"the symbol {symbol!r} is declared here and already "
                            f"at {seen[symbol]}, and record 0005 has one "
                            "declaration per object so that two mentions of it "
                            "cannot disagree about how it behaves"
                        ),
                    )
                )
                continue
            seen[symbol] = where
    return found


def _declaration_refusals(
    document: dict[str, object], index: dict[str, positions.Position]
) -> list[Refusal]:
    """Every reason a field declaration cannot be built as it is written."""
    found: list[Refusal] = []
    for number, member in enumerate(listing(document, "fields")):
        role = text(member, "role")
        where = f"fields[{number}].role"
        slots = representation.SLOTS.get(role)
        if slots is None:
            found.append(
                Refusal(
                    rule="unknown-role",
                    where=where,
                    at=positions.nearest(index, where),
                    named=role,
                    detail=(
                        f"the field role {role!r} has no number of index slots "
                        "written for it, so a declaration for it cannot be built "
                        "and the symmetries on it cannot be judged. The roles "
                        "that do are " + ", ".join(sorted(representation.SLOTS))
                    ),
                )
            )
            continue
        found.extend(_symmetry_refusals(member, number, slots, role, index))
    return found


def _symmetry_refusals(
    member: dict[str, object],
    number: int,
    slots: int,
    role: str,
    index: dict[str, positions.Position],
) -> list[Refusal]:
    """The symmetries on one declaration, judged against the slots it has."""
    found: list[Refusal] = []
    for position, symmetry in enumerate(symmetries(member)):
        where = f"fields[{number}].symmetries[{position}]"
        needs = representation.SYMMETRIES.get(symmetry)
        if needs is None:
            found.append(
                Refusal(
                    rule="unknown-symmetry",
                    where=where,
                    at=positions.nearest(index, where),
                    named=symmetry,
                    detail=(
                        f"the symmetry {symmetry!r} is not one this "
                        "representation has a case for, and the ones it has are "
                        + ", ".join(sorted(representation.SYMMETRIES))
                    ),
                )
            )
        elif slots < needs:
            found.append(
                Refusal(
                    rule="symmetry-without-slots",
                    where=where,
                    at=positions.nearest(index, where),
                    named=symmetry,
                    detail=(
                        f"the symmetry {symmetry!r} is a statement about {needs} "
                        f"index slots and a field in the role {role!r} has "
                        f"{slots}, so there is nothing here for it to be a "
                        "statement about"
                    ),
                )
            )
    return found


def _declarations(document: dict[str, object]) -> tuple[representation.Tensor, ...]:
    """The field declarations, built once, so every mention resolves to the same one."""
    return tuple(
        representation.Tensor(
            symbol=text(member, "symbol"),
            role=text(member, "role"),
            slots=representation.SLOTS[text(member, "role")],
            symmetries=symmetries(member),
        )
        for member in listing(document, "fields")
    )


def _resolve(
    document: dict[str, object],
    declared: tuple[representation.Tensor, ...],
    index: dict[str, positions.Position],
) -> tuple[list[representation.Term], list[Refusal]]:
    """Every term with its mentions resolved to declarations, or why one is not."""
    terms: list[representation.Term] = []
    found: list[Refusal] = []
    for number, term in enumerate(_terms(document)):
        head = text(term, "head")
        where = f"lagrangian.terms[{number}].head"
        needs = HEAD_NEEDS.get(head)
        if needs is None:
            found.append(
                Refusal(
                    rule="unresolved-head",
                    where=where,
                    at=positions.nearest(index, where),
                    named=head,
                    detail=(
                        f"the term head {head!r} is one this reader has nothing "
                        "written for, so there is no field it could be resolved "
                        "against and it does not reach the representation"
                    ),
                )
            )
            continue
        mentions: list[representation.Tensor] = []
        for requirement in needs:
            wanted = " or ".join(sorted(requirement))
            candidates = [one for one in declared if one.role in requirement]
            if not candidates:
                found.append(
                    Refusal(
                        rule="undeclared-field",
                        where=where,
                        at=positions.nearest(index, where),
                        named=head,
                        detail=(
                            f"the term {head!r} is built from a field in the "
                            f"role {wanted}, and this document declares none"
                        ),
                    )
                )
                continue
            if len(candidates) > 1:
                found.append(
                    Refusal(
                        rule="ambiguous-field",
                        where=where,
                        at=positions.nearest(index, where),
                        named=head,
                        detail=(
                            f"the term {head!r} is built from a field in the "
                            f"role {wanted}, and this document declares "
                            + ", ".join(one.symbol for one in candidates)
                            + ", so the mention resolves to no single declaration"
                        ),
                    )
                )
                continue
            mentions.append(candidates[0])
        terms.append(
            representation.Term(
                head=head,
                coefficient=text(term, "coefficient"),
                mentions=tuple(mentions),
            )
        )
    return terms, found


def _action(
    document: dict[str, object],
    declared: tuple[representation.Tensor, ...],
    terms: list[representation.Term],
) -> representation.Action:
    """The action itself, once nothing about the document is left to refuse."""
    metadata = mapping(document, "metadata")
    manifold = mapping(document, "manifold")
    matter = mapping(document, "matter")
    regime = mapping(document, "regime")
    return representation.Action(
        schema_version=count(document, "schema_version"),
        metadata=representation.Metadata(
            identifier=text(metadata, "identifier"),
            name=text(metadata, "name"),
            citation=text(metadata, "citation"),
        ),
        manifold=representation.Manifold(
            dimension=count(manifold, "dimension"),
            signature=text(manifold, "signature"),
        ),
        fields=declared,
        lagrangian=representation.Lagrangian(terms=tuple(terms)),
        matter=representation.Matter(
            coupling=text(matter, "coupling"),
            frame=text(matter, "frame"),
        ),
        parameters=tuple(
            representation.Parameter(
                symbol=text(member, "symbol"),
                minimum=bound(member, "minimum"),
                maximum=bound(member, "maximum"),
                claimed_by=text(member, "claimed_by"),
            )
            for member in listing(document, "parameters")
        ),
        regime=representation.Regime(
            name=text(regime, "name"),
            length_scale=text(regime, "length_scale"),
        ),
    )


def _carried(refusal: schema.Refusal, index: dict[str, positions.Position]) -> Refusal:
    """A refusal the schema made, given the line and column its path resolves to.

    The schema writes a path at `where` for every rule but one. Bytes the loader
    could not read have no path, so that refusal writes the place in the text
    instead, and it arrives here as a refusal about the document as a whole with
    the loader's own line and column already in the index.
    """
    where = "" if refusal.where.startswith("line ") else refusal.where
    return Refusal(
        rule=refusal.rule,
        where=where,
        at=positions.nearest(index, where),
        named=refusal.named,
        detail=refusal.detail,
    )


def read(
    document_text: str,
) -> tuple[representation.Action | None, tuple[Refusal, ...]]:
    """The bytes of a document, as an action or as every reason it is not one.

    Every reason rather than the first, which is the schema's rule and holds
    here for the same cause: an author fixing one refusal per run learns about
    the next one a run later, and these come in groups.

    An action and a refusal are never both returned. A partly built action is a
    thing a later stage could read, and a stage that read one would be deriving
    field equations for a theory nobody wrote.
    """
    index = positions.of(document_text)
    loaded, unreadable = schema.read(document_text)
    if unreadable:
        return None, tuple(_carried(refusal, index) for refusal in unreadable)
    # Past the schema, so the document is a mapping carrying every key the
    # schema requires, of the kinds it admits. Everything below reads what the
    # schema has already admitted.
    document: dict[str, object] = loaded if isinstance(loaded, dict) else {}
    found = _symbol_refusals(document, index)
    found.extend(_declaration_refusals(document, index))
    if found:
        return None, tuple(found)
    declared = _declarations(document)
    terms, unresolved = _resolve(document, declared, index)
    if unresolved:
        return None, tuple(unresolved)
    return _action(document, declared, terms), ()


def emit(action: representation.Action) -> str:
    """The document an action came from, written back out.

    Not the bytes it was read from. Whitespace, key order and the spelling of a
    number belong to the document and not to the action, so a round trip
    comparing bytes would be testing the formatting rather than the property
    issue #25 asks for, which is that reading and writing are inverse on the
    representation.

    The keys are written in the order the schema declares them, so a document
    that went through here reads like the ones in the tree rather than in
    whichever order a mapping happened to hold them.
    """
    document = {
        "schema_version": action.schema_version,
        "metadata": {
            "identifier": action.metadata.identifier,
            "name": action.metadata.name,
            "citation": action.metadata.citation,
        },
        "manifold": {
            "dimension": action.manifold.dimension,
            "signature": action.manifold.signature,
        },
        "fields": [
            {
                "symbol": declared.symbol,
                "role": declared.role,
                "symmetries": list(declared.symmetries),
            }
            for declared in action.fields
        ],
        "lagrangian": {
            "terms": [
                {"head": term.head, "coefficient": term.coefficient}
                for term in action.lagrangian.terms
            ]
        },
        "matter": {
            "coupling": action.matter.coupling,
            "frame": action.matter.frame,
        },
        "parameters": [
            {
                "symbol": parameter.symbol,
                "minimum": parameter.minimum,
                "maximum": parameter.maximum,
                "claimed_by": parameter.claimed_by,
            }
            for parameter in action.parameters
        ],
        "regime": {
            "name": action.regime.name,
            "length_scale": action.regime.length_scale,
        },
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"
