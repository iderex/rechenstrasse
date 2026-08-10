"""Varying the action with respect to the metric.

Issue #30. This is the first stage that computes rather than reads. It takes the
action of record 0005 and produces the field equations of the gravitational
sector, in the sign, index and unit conventions record 0008 fixes.

What it produces, and in which normalisation. The value below is `E_mn`, the
functional derivative of the gravitational part of the action with respect to
the inverse metric, with the volume element divided back out:

    E_mn = (1 / sqrt(-g)) delta( sqrt(-g) L ) / delta g^{mn}

The field equation is `E_mn = 1/2 T_mn`, with `T_mn` the stress-energy tensor of
the matter action. This stage does not read the matter sector and does not
produce `T_mn`: the documents declare a coupling and a frame and nothing else,
and building a stress-energy tensor out of those two words is the guess record
0004 rules out. So what is here is one side of an equation whose other side is
`1/2 T_mn`, and a published field equation is compared against it by dividing
that equation by twice the coupling, which the suite does in the place it does
it.

How an expression is held. A field equation in this class is a sum of rank two
symmetric structures with scalar coefficients, and the structures are the small
set in `KINDS` below. That carries every term the covered heads produce and it
is not a general tensor algebra: there is no free index type here, for the
reason `rechenstrasse.representation` gives, and no canonicalisation under index
symmetry either. The seam record 0005 draws for that is issue #33 and nothing
here reaches through it.

The one normalisation this module performs is linearity of the second derivative
operators over the constants of the theory. `grad_m grad_n (u / c)` with `c`
constant is held as `1/c` times `grad_m grad_n u`, and a second derivative of
something with no dynamical content in it is dropped, because it is zero.
Without that, two expressions that are equal would sit on different structures
and the exact comparison record 0006 requires would be a comparison of
spellings. Which symbols are constant is read off the document rather than
guessed: the parameters it declares, the coefficients of the heads whose
coefficient is a constant, and Newton's constant, which record 0008 keeps
visible in the coupling.

What the variation does with the connection. The variation of the curvature
scalar carries two pieces in which the derivative sits on the variation of the
metric rather than on anything else, and those two are what the variation of the
connection collapses to:

    delta( sqrt(-g) u R ) / delta g^{mn}
        = sqrt(-g) ( u R_mn - 1/2 u R g_mn )
        + sqrt(-g) u ( g_mn box - grad_m grad_n ) delta g^{mn}

`integrate_by_parts` moves those two derivatives off the variation and onto `u`,
which is the step that turns them into `g_mn box u - grad_m grad_n u` and leaves
two total divergences behind. It is the only place in this module where a
boundary term is created, which is what makes it the only place one can be lost.

Issue #32 is why those divergences are values rather than a comment. `derive`
returns them beside the equation, so an equation and the assumptions it was
reached under travel together, and a reader of a derivation can see which
boundary terms were taken to vanish. What no output carries them into is a run
record: record 0007's provenance block is issue #60 and does not exist, so
today they reach the caller of this stage and nothing further.

Which heads this stage has a rule for. All of them, which is the covered set of
the admissibility gate and nothing else. Four of the five rules reach terms
built from the metric, its inverse, the curvature scalar and a scalar field with
first derivatives, which is the class issue #30 names. `horndeski_g3` is the one
outside that class, because the term it stands for carries `box phi`, and its
rule is issue #114. The suite holds the covered set against `RULES`, so a head
widened into the gate cannot arrive here as a term nobody varies.

What the cubic term needs that the others do not. `-G3(phi, X) box phi` puts a
second derivative of the field under the variation, and the variation of the
connection inside it reaches `G3` only through an integration by parts, whose
derivative then comes off `G3` through both of its arguments. So the equation it
contributes carries two things no other rule produces: the gradient of the
kinetic scalar paired with the gradient of the field, which is the structure
`MIXED_GRADIENT_PAIR`, and two scalars this module has no metric to contract,
`BOX` and `GRADIENT_PRODUCT`, which are held as atoms for the same reason the
curvature scalar is.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

import sympy as sp

from rechenstrasse import representation

# The rank two symmetric structures a field equation in this class is built
# from. Each is a shape rather than a value, and what stands in front of it is a
# scalar expression.
#
#   ricci                 R_mn
#   metric                g_mn
#   gradient-pair         grad_m phi grad_n phi
#   mixed-gradient-pair   grad_(m u grad_n) phi, with u the scalar it carries
#   hessian               grad_m grad_n u, with u the scalar it carries
#   box-times-metric      g_mn box u, with u the scalar it carries
#
# The last three carry a scalar and the first two do not, and a structure of one
# of those kinds holding one would be a value with two meanings.
#
# The mixed pair is symmetrised over its two indices and its second gradient is
# always the scalar field, so the one scalar it holds is the other gradient. It
# prints the field as `phi`, which is what the plain gradient pair above already
# does.
RICCI: Final = "ricci"
METRIC: Final = "metric"
GRADIENT_PAIR: Final = "gradient-pair"
MIXED_GRADIENT_PAIR: Final = "mixed-gradient-pair"
HESSIAN: Final = "hessian"
BOX_TIMES_METRIC: Final = "box-times-metric"

KINDS: Final[tuple[str, ...]] = (
    RICCI,
    METRIC,
    GRADIENT_PAIR,
    MIXED_GRADIENT_PAIR,
    HESSIAN,
    BOX_TIMES_METRIC,
)
CARRY_A_SCALAR: Final[frozenset[str]] = frozenset(
    {MIXED_GRADIENT_PAIR, HESSIAN, BOX_TIMES_METRIC}
)

# The curvature scalar, and the kinetic scalar record 0008 defines as
# X = -1/2 g^{mn} (grad_m phi)(grad_n phi). Both are symbols here rather than
# expressions, because this module holds no metric to contract with.
CURVATURE_SCALAR: Final = sp.Symbol("R")
KINETIC_SCALAR: Final = sp.Symbol("X")

# Two more scalars, written on the scalars they are built from rather than held
# as bare symbols, for the same reason the two above are symbols: this module has
# no metric to contract with, so a contraction is an atom here and not an
# expression. `BOX(u)` is `box u`, and `GRADIENT_PRODUCT(u, v)` is
# `grad^a u grad_a v`. Both reach an equation only through the cubic term.
BOX: Final = sp.Function("box")
GRADIENT_PRODUCT: Final = sp.Function("grad_dot_grad")

# The gravitational coupling in the spelling record 0008 requires. `G` stays
# visible rather than being set to one, so that the constant in the field
# equations and the constant a Cavendish experiment measures do not become one
# symbol at the stage that exists to tell them apart.
NEWTON_CONSTANT: Final = sp.Symbol("G")
COUPLING: Final = 8 * sp.pi * NEWTON_CONSTANT

# The heads whose coefficient is a constant of the theory rather than a function
# of the field. A coefficient here is one symbol; a coefficient anywhere else is
# an undefined function of the arguments its head is written with.
CONSTANT_COEFFICIENT_HEADS: Final[frozenset[str]] = frozenset(
    {"ricci_scalar", "cosmological_constant"}
)

# What every boundary term this stage drops is dropped under. Written once and
# carried on each dropped term, because an assumption stated in a docstring is
# one the reader of a result never sees.
BOUNDARY_ASSUMPTION: Final = (
    "the variation of the metric and its first derivative vanish on the "
    "boundary of the region the action is integrated over"
)

# What the cubic term's boundary terms are dropped under, which is less than the
# line above asks for. Its divergences come from one integration by parts rather
# than two, so nothing about the first derivative of the variation is needed, and
# carrying the stronger sentence on them would say the derivation assumed
# something it did not.
METRIC_VARIATION_ASSUMPTION: Final = (
    "the variation of the metric vanishes on the boundary of the region the "
    "action is integrated over"
)

# Every assumption a boundary term in this module can go under. The suite reads
# this rather than a single sentence, so a rule that invented a third one would
# be caught instead of passing as prose nobody compares.
BOUNDARY_ASSUMPTIONS: Final[frozenset[str]] = frozenset(
    {BOUNDARY_ASSUMPTION, METRIC_VARIATION_ASSUMPTION}
)


@dataclass(frozen=True)
class Structure:
    """One rank two symmetric shape, and the scalar it is a derivative of.

    `scalar` is `None` for a kind that carries none. Two structures compare
    equal when they are the same shape of the same scalar, which is what lets a
    field equation be coefficients standing on structures.
    """

    kind: str
    scalar: sp.Expr | None = None

    def sort_key(self) -> tuple[int, str]:
        written = "" if self.scalar is None else sp.srepr(self.scalar)
        return (KINDS.index(self.kind), written)

    def __str__(self) -> str:
        if self.kind == HESSIAN:
            return f"grad_m grad_n ({self.scalar})"
        if self.kind == BOX_TIMES_METRIC:
            return f"g_mn box ({self.scalar})"
        if self.kind == MIXED_GRADIENT_PAIR:
            return f"grad_(m ({self.scalar}) grad_n) phi"
        if self.kind == RICCI:
            return "R_mn"
        if self.kind == GRADIENT_PAIR:
            return "grad_m phi grad_n phi"
        return "g_mn"


@dataclass(frozen=True)
class FieldEquation:
    """`E_mn`, as coefficients on structures, with the constants it was read in.

    `terms` is sorted and carries no structure whose coefficient vanishes, so
    two equations that are the same expression are the same value and the
    comparison is the language's own equality.
    """

    terms: tuple[tuple[Structure, sp.Expr], ...]
    constants: frozenset[sp.Symbol]

    def coefficient(self, structure: Structure) -> sp.Expr:
        """What stands in front of one structure, and zero where it is absent."""
        for held, standing in self.terms:
            if held == structure:
                return standing
        return sp.Integer(0)

    def minus(self, other: "FieldEquation") -> "FieldEquation":
        """This equation less another one, read in the constants of this one."""
        return _assemble(
            list(self.terms) + [(shape, -standing) for shape, standing in other.terms],
            self.constants,
        )

    def is_zero(self) -> bool:
        """Whether every coefficient vanishes.

        Exact, with no tolerance anywhere in it, which is record 0006's
        condition on the comparison this pipeline rests on.
        """
        return self.terms == ()

    def __str__(self) -> str:
        return " + ".join(f"({standing}) {shape}" for shape, standing in self.terms)


@dataclass(frozen=True)
class SurfaceTerm:
    """One total divergence the variation dropped, and what dropping it assumes.

    Issue #32. A boundary term discarded without being named is a defect that
    surfaces much later as a factor nobody can find, so the discard is a value
    here rather than a comment.

    `around` is the scalar the divergence is built from, `divergence` is the
    thing itself written out, and `assumed` is the condition under which it may
    be dropped. `vanishes_by_itself` is true where the divergence has a half that
    is zero because that scalar is constant, in which case only the surviving
    half is written. The flag is not a statement that the term vanished: the
    reader of a derivation wants to know which boundary terms were assumed away
    and which of those had a part that went away on its own. A divergence that
    was never in two halves, which is what one integration by parts leaves,
    carries it false whatever the scalar is.
    """

    around: sp.Expr
    divergence: str
    assumed: str
    vanishes_by_itself: bool

    def __str__(self) -> str:
        return f"{self.divergence}, dropped assuming {self.assumed}"


@dataclass(frozen=True)
class Derivation:
    """What one variation produced: the equation, and everything it threw away.

    The two travel together because they are one result. An equation read
    without the boundary terms that were dropped to reach it is an equation
    whose assumptions the reader cannot see, which is the failure issue #32 is
    about.
    """

    equation: FieldEquation
    surface_terms: tuple[SurfaceTerm, ...]


@dataclass(frozen=True)
class NotDerived:
    """Why this stage produced no field equation for a document.

    A different thing from a refusal in `rechenstrasse.refusal`. A refusal says
    a decision record drew a line the input is outside. This says the work that
    would derive the input has not been written. Reporting the two in one
    vocabulary would tell an author their theory was ruled out when it was not.

    Every covered head has a rule, so no document the gate admits reaches this
    today. What still does is a term whose head this stage never heard of, and a
    term that resolved to no scalar field for a head whose coefficient needs one.
    """

    reasons: tuple[str, ...]


def _split_constant(
    expression: sp.Expr, constants: frozenset[sp.Symbol]
) -> tuple[sp.Expr, sp.Expr]:
    """One product, split into the part that is constant and the part that is not.

    A factor is constant when every symbol in it is one the document declared
    constant. Nothing here decides a factor is constant because it looks like
    one.
    """
    constant_part = sp.Integer(1)
    varying_part = sp.Integer(1)
    for factor in sp.Mul.make_args(expression):
        if factor.free_symbols <= constants:
            constant_part = constant_part * factor
        else:
            varying_part = varying_part * factor
    return constant_part, varying_part


def _derivative_of(
    kind: str,
    scalar: sp.Expr,
    coefficient: sp.Expr,
    constants: frozenset[sp.Symbol],
) -> list[tuple[Structure, sp.Expr]]:
    """A derivative operator applied to a scalar, by linearity.

    Two things come out of this that a structure holding the scalar whole would
    not give. A constant factor comes out in front, so the same expression
    written two ways is one structure. And a derivative of something with no
    dynamical content is dropped, because it is zero rather than small, which is
    what makes the constant coefficient of the Einstein-Hilbert term produce no
    derivative terms at all.

    Every kind in `CARRY_A_SCALAR` differentiates its scalar, so all of them come
    through here: the two second derivative operators, and the single gradient
    the mixed pair holds.
    """
    produced: list[tuple[Structure, sp.Expr]] = []
    for piece in sp.Add.make_args(sp.expand(scalar)):
        constant_part, varying_part = _split_constant(piece, constants)
        if varying_part == sp.Integer(1):
            continue
        produced.append((Structure(kind, varying_part), coefficient * constant_part))
    return produced


def _assemble(
    terms: list[tuple[Structure, sp.Expr]], constants: frozenset[sp.Symbol]
) -> FieldEquation:
    """Collect coefficients onto structures, drop the ones that vanish, sort."""
    collected: dict[Structure, sp.Expr] = {}
    for shape, standing in terms:
        collected[shape] = collected.get(shape, sp.Integer(0)) + standing
    kept: list[tuple[Structure, sp.Expr]] = []
    for shape, standing in collected.items():
        settled = sp.simplify(standing)
        if settled != sp.Integer(0):
            kept.append((shape, settled))
    kept.sort(key=lambda entry: entry[0].sort_key())
    return FieldEquation(terms=tuple(kept), constants=constants)


def integrate_by_parts(
    coefficient: sp.Expr, constants: frozenset[sp.Symbol]
) -> tuple[list[tuple[Structure, sp.Expr]], tuple[SurfaceTerm, ...]]:
    """Move the two derivatives of the curvature variation off the variation.

    Issue #32. This is the named operation, and it is the only place in this
    module where a boundary term is created, so it is the only place one can be
    lost. What goes in is the scalar `u` standing in front of the curvature
    scalar, and what the variation carries at that point is

        sqrt(-g) u ( g_mn box - grad_m grad_n ) delta g^{mn}

    Each of the two is integrated by parts twice. What comes back is the pair
    that acts on `u` instead, and every total divergence that was dropped to get
    there, written out.

    Each integration by parts leaves one divergence, so two of them leave two,
    and each divergence has two halves: the derivative that was still on the
    variation, and the one that came off `u`. Where `u` is constant the second
    half is zero and is not written, because a report that prints a term the
    derivation never dropped is as bad as one that hides a term it did.
    """
    moved = _derivative_of(
        BOX_TIMES_METRIC, coefficient, sp.Integer(1), constants
    ) + _derivative_of(HESSIAN, coefficient, sp.Integer(-1), constants)
    against_the_variation = (
        ("l", f"({coefficient}) g_mn grad_l delta g^(mn)"),
        ("m", f"({coefficient}) grad^n delta g_(mn)"),
    )
    off_the_coefficient = (
        f"g_mn delta g^(mn) grad_l ({coefficient})",
        f"delta g_(mn) grad^n ({coefficient})",
    )
    constant = coefficient.free_symbols <= constants
    dropped: list[SurfaceTerm] = []
    for (index, first), second in zip(
        against_the_variation, off_the_coefficient, strict=True
    ):
        written = first if constant else f"{first} - {second}"
        dropped.append(
            SurfaceTerm(
                around=coefficient,
                divergence=f"grad^{index} ( {written} )",
                assumed=BOUNDARY_ASSUMPTION,
                vanishes_by_itself=constant,
            )
        )
    return moved, tuple(dropped)


def _vary_curvature_scalar(
    coefficient: sp.Expr, constants: frozenset[sp.Symbol]
) -> tuple[list[tuple[Structure, sp.Expr]], tuple[SurfaceTerm, ...]]:
    """The variation of `u R`, with the connection pieces moved onto `u`.

    The first two terms are what the variation of the inverse metric and of the
    volume element give directly. The rest is the variation of the connection,
    which reaches `u` only through the integration by parts above, and which is
    the only part of this module that drops anything.
    """
    pointwise = [
        (Structure(RICCI), coefficient),
        (Structure(METRIC), -sp.Rational(1, 2) * coefficient * CURVATURE_SCALAR),
    ]
    moved, dropped = integrate_by_parts(coefficient, constants)
    return pointwise + moved, dropped


def _vary_g2(
    coefficient: sp.Expr, _constants: frozenset[sp.Symbol]
) -> tuple[list[tuple[Structure, sp.Expr]], tuple[SurfaceTerm, ...]]:
    """The variation of `G2(phi, X)`.

    The metric reaches this term twice: through the volume element, and through
    the kinetic scalar, whose variation with respect to the inverse metric is
    `-1/2 grad_m phi grad_n phi` under record 0008's definition of `X`. Neither
    route puts a derivative on the variation, so nothing is integrated by parts
    and no boundary term is dropped.
    """
    return [
        (
            Structure(GRADIENT_PAIR),
            -sp.Rational(1, 2) * sp.Derivative(coefficient, KINETIC_SCALAR).doit(),
        ),
        (Structure(METRIC), -sp.Rational(1, 2) * coefficient),
    ], ()


def _vary_g3(
    coefficient: sp.Expr, _constants: frozenset[sp.Symbol]
) -> tuple[list[tuple[Structure, sp.Expr]], tuple[SurfaceTerm, ...]]:
    """The variation of `-G3(phi, X) box phi`, which is issue #114.

    The metric reaches this term four ways, and the last of them is what makes it
    a piece of work rather than a fifth line in a table. Through the volume
    element. Through the kinetic scalar inside `G3`. Through the inverse metric
    that contracts the two derivatives in `box phi`. And through the connection
    inside `box phi`, which no other covered head carries, because no other one
    puts a second derivative of the field under the variation.

    The connection piece contracts to

        g^ab delta Gamma^c_ab grad_c phi

    with two terms in it, and each is integrated by parts once to take the
    derivative off the variation of the metric. What comes back sits on `G3`, and
    the derivative that came off it reaches both of its arguments:

        grad_a G3 = G3_phi grad_a phi + G3_X grad_a X

    Two cancellations happen on the way and both are worth naming, because a
    reader who expects the second derivatives of `phi` to survive will look for
    them. The `G3 grad_m grad_n phi` the inverse metric produces is cancelled
    exactly by the one the integration by parts brings back, and the
    `1/2 G3 box phi g_mn` from the volume element is cancelled exactly by the
    half of the second divergence that carries `box phi`. So the equation carries
    no undifferentiated `G3` at all, which is why a constant `G3` contributes
    nothing: the term is then a total divergence.

    What is left is the published form, in record 0008's conventions:

        1/2 G3_X box phi grad_m phi grad_n phi
        + G3_phi grad_m phi grad_n phi
        + G3_X grad_(m X grad_n) phi
        + X G3_phi g_mn
        - 1/2 G3_X grad^a X grad_a phi g_mn

    The field is read off the coefficient rather than passed in, because
    `coefficient_of` is what put it there: the coefficient of this head is an
    undefined function of the field and the kinetic scalar, in that order.
    """
    field = coefficient.args[0]
    by_the_field = sp.Derivative(coefficient, field).doit()
    by_the_kinetic = sp.Derivative(coefficient, KINETIC_SCALAR).doit()
    produced = [
        (
            Structure(GRADIENT_PAIR),
            by_the_field + sp.Rational(1, 2) * by_the_kinetic * BOX(field),
        ),
        (Structure(MIXED_GRADIENT_PAIR, KINETIC_SCALAR), by_the_kinetic),
        (
            Structure(METRIC),
            KINETIC_SCALAR * by_the_field
            - sp.Rational(1, 2)
            * by_the_kinetic
            * GRADIENT_PRODUCT(KINETIC_SCALAR, field),
        ),
    ]
    # One integration by parts per term of the contracted connection piece, so
    # one divergence each and neither of them in two halves. What a document
    # holds constant decides nothing here: a `G3` that varies with nothing leaves
    # the same two divergences, since what they are built from is the gradient of
    # the field rather than the gradient of the coefficient.
    dropped = tuple(
        SurfaceTerm(
            around=coefficient,
            divergence=written,
            assumed=METRIC_VARIATION_ASSUMPTION,
            vanishes_by_itself=False,
        )
        for written in (
            f"grad^n ( ({coefficient}) grad_m ({field}) delta g^(mn) )",
            f"grad^l ( -1/2 ({coefficient}) grad_l ({field}) g_mn delta g^(mn) )",
        )
    )
    return produced, dropped


def _vary_cosmological_constant(
    coefficient: sp.Expr, _constants: frozenset[sp.Symbol]
) -> tuple[list[tuple[Structure, sp.Expr]], tuple[SurfaceTerm, ...]]:
    """The variation of the constant term, in record 0008's normalisation.

    Record 0008 fixes the field equations as `G_mn + Lambda g_mn = 8 pi G T_mn`,
    and this head is that term: the coefficient a document writes here is that
    `Lambda` rather than the number standing in the Lagrangian, so the Lagrangian
    term the head stands for is `-Lambda / (8 pi G)` and its variation is below.

    What that reading costs, said rather than left to be found. It ties the head
    to the Einstein-Hilbert normalisation `R / (16 pi G)`, and schema version 1
    has no key for what a coefficient means, so a document pairing this head with
    a curvature term normalised any other way carries a `Lambda` that is not
    record 0008's, and nothing in this tree refuses that document.
    """
    return [(Structure(METRIC), coefficient / (2 * COUPLING))], ()


# One rule per head this stage varies. `derive` dispatches on this mapping, and
# the suite holds its keys against the covered heads of the admissibility gate,
# which is what stops a head being widened into the gate with nothing to vary it.
# A rule returns what it contributes to the equation and every boundary term it
# dropped, in that order, so a rule that drops one cannot return without saying
# so.
Rule = Callable[
    [sp.Expr, frozenset[sp.Symbol]],
    tuple[list[tuple[Structure, sp.Expr]], tuple[SurfaceTerm, ...]],
]

RULES: Final[dict[str, Rule]] = {
    "ricci_scalar": _vary_curvature_scalar,
    "horndeski_g4": _vary_curvature_scalar,
    "horndeski_g2": _vary_g2,
    "horndeski_g3": _vary_g3,
    "cosmological_constant": _vary_cosmological_constant,
}


def _scalar_symbol(term: representation.Term) -> sp.Symbol | None:
    """The scalar field a term resolved to, or nothing where it resolved to none.

    Record 0005 puts the declarations on the term, so this reads the term rather
    than searching the action. A term the reader of issue #25 built always
    carries one where its head needs one, because `undeclared-field` refuses the
    document otherwise, and a term that does not is one nothing in this tree
    built.
    """
    for mention in term.mentions:
        if mention.role == "scalar":
            return sp.Symbol(mention.symbol)
    return None


def constants_of(action: representation.Action) -> frozenset[sp.Symbol]:
    """Every symbol this action holds constant.

    The parameters the document declares, the coefficients of the heads whose
    coefficient is a constant, and Newton's constant, which record 0008 keeps
    visible in the coupling rather than absorbing into a normalisation.
    """
    held = {sp.Symbol(parameter.symbol) for parameter in action.parameters}
    held.add(NEWTON_CONSTANT)
    for term in action.lagrangian.terms:
        if term.head in CONSTANT_COEFFICIENT_HEADS:
            held.add(sp.Symbol(term.coefficient))
    return frozenset(held)


def coefficient_of(term: representation.Term) -> sp.Expr | None:
    """The symbol or the undefined function standing in front of one term.

    A constant coefficient is a symbol. Every other coefficient is an undefined
    function of the arguments its head is written with, which is what lets a
    derivative of it survive to the comparison instead of being evaluated into
    something the document never said. `horndeski_g4` is a function of the field
    alone, which is what separates that head from the kinetic one the gate
    refuses.
    """
    if term.head in CONSTANT_COEFFICIENT_HEADS:
        return sp.Symbol(term.coefficient)
    scalar = _scalar_symbol(term)
    if scalar is None:
        return None
    if term.head == "horndeski_g4":
        return sp.Function(term.coefficient)(scalar)
    return sp.Function(term.coefficient)(scalar, KINETIC_SCALAR)


def field_equation(action: representation.Action) -> FieldEquation | NotDerived:
    """`E_mn` alone, for a caller that has no use for what was dropped.

    A convenience over `derive` and nothing more. It is not the way to get an
    equation whose assumptions a reader has to see: the surface terms are part
    of the result rather than a detail of how it was reached, which is why the
    fuller value is the one with its own name.
    """
    produced = derive(action)
    if isinstance(produced, NotDerived):
        return produced
    return produced.equation


def derive(action: representation.Action) -> Derivation | NotDerived:
    """`E_mn` for one action with every boundary term it dropped, or why not.

    Every term contributes or the document produces no equation at all, because
    a field equation missing one term of the action is wrong in the way that
    looks right.
    """
    reasons: list[str] = []
    varied: list[tuple[representation.Term, sp.Expr]] = []
    for term in action.lagrangian.terms:
        if term.head not in RULES:
            reasons.append(
                f"{term.head}: this stage has no variation rule for that head"
            )
            continue
        coefficient = coefficient_of(term)
        if coefficient is None:
            reasons.append(
                f"{term.head}: the term resolved to no scalar field, and the "
                "coefficient of that head is a function of one"
            )
            continue
        varied.append((term, coefficient))
    if reasons:
        return NotDerived(reasons=tuple(reasons))
    constants = constants_of(action)
    produced: list[tuple[Structure, sp.Expr]] = []
    dropped: list[SurfaceTerm] = []
    for term, coefficient in varied:
        contribution, boundary = RULES[term.head](coefficient, constants)
        produced.extend(contribution)
        dropped.extend(boundary)
    return Derivation(
        equation=_assemble(produced, constants), surface_terms=tuple(dropped)
    )


def substituting(
    equation: FieldEquation, readings: tuple[dict[sp.Expr, sp.Expr], ...]
) -> FieldEquation:
    """The same equation with a reading of its coefficients put in.

    A document says which terms a theory carries and which symbol stands in
    front of each, and schema version 1 has no key for what those symbols mean.
    A comparison against a published equation needs that meaning, so it is
    supplied here, beside the comparison, and is never inferred from the name of
    a symbol.

    The readings are applied in the order they are given, because one of them
    can put a symbol into an expression that a later one reads. The structures
    are rebuilt rather than substituted into, because a reading that puts a
    constant factor inside a second derivative has to come back out for the
    comparison to be an equality of expressions rather than of spellings.
    """

    def put_in(expression: sp.Expr) -> sp.Expr:
        settled = expression
        for reading in readings:
            settled = settled.subs(reading).doit()
        return sp.simplify(settled)

    rebuilt: list[tuple[Structure, sp.Expr]] = []
    for shape, standing in equation.terms:
        if shape.kind in CARRY_A_SCALAR:
            rebuilt.extend(
                _derivative_of(
                    shape.kind,
                    put_in(shape.scalar),
                    put_in(standing),
                    equation.constants,
                )
            )
        else:
            rebuilt.append((shape, put_in(standing)))
    return _assemble(rebuilt, equation.constants)
