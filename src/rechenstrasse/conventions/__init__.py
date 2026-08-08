"""The sign, index and unit conventions of record 0008, in one place.

Issue #8. The record fixes a set of conventions and says that each one becomes
one named constant or one documented function rather than an assumption repeated
in several modules. This is that place. A stage that needs the signature reads
`SIGNATURE`; a stage that needs the Riemann tensor calls `riemann`; nothing
writes down the sign of anything a second time.

The failure this exists against is not a stage that gets a convention wrong. It
is two stages that get it differently right. A flipped Riemann sign does not
produce nonsense, it produces field equations that are structurally correct and
off by a minus, and those survive review and surface much later as a parity
comparison nobody can localise.

Everything here is exact. There is no float literal in this module and there may
not be one, which is record 0006's boundary and the rule
`no-float-above-the-boundary` in `tools/invariants.py` refusing it.

What this module is written on. The internal representation of record 0005 is an
expression over tensor terms with abstract indices, and it does not exist yet.
So the functions below take explicit components: a metric as a matrix and a list
of coordinate symbols, which is what the tree can carry today. What the record
asks for is that the sign choices live in one named place, and that is true of
these definitions whether the thing they are later called with is a component
array or an abstract-index term. When the representation lands, the definitions
move to it and the constants do not move at all.

What is not fixed here. Nothing refuses a stage that computes a Christoffel
symbol by hand instead of calling `christoffel`, because no reading of this tree
tells one from the other. The record says the conventions live in one place; a
machine holds them there, and a person keeps them used.
"""

from collections.abc import Callable, Sequence
from itertools import permutations
from math import factorial

import sympy

# The metric signature, and the constant every stage reads instead of assuming
# one. A timelike interval is negative.
SIGNATURE: tuple[int, int, int, int] = (-1, 1, 1, 1)

# What a reader compares against a textbook page. Spelled out rather than left
# to be inferred from the tuple above, because the tuple is a data structure and
# this is the thing people say out loud.
SIGNATURE_NAME = "(-, +, +, +)"

# Geometrised in the speed of light only. Record 0008 is explicit that the
# gravitational coupling stays visible, so there is no constant here setting it
# to one and `NEWTON_CONSTANT` below is a symbol that survives into the output.
SPEED_OF_LIGHT = sympy.Integer(1)

# The gravitational coupling as it appears in the field equations. In a
# scalar-tensor theory this is a different number from the one a Cavendish
# experiment measures, and the relation between them is part of what the
# post-Newtonian stage computes, so absorbing either into the other would make
# the difference invisible at the stage that exists to measure it.
NEWTON_CONSTANT = sympy.Symbol("G", positive=True)
COUPLING = 8 * sympy.pi * NEWTON_CONSTANT

# The cosmological constant, one symbol, carried on the geometry side. A theory
# that writes it as a constant term in a potential declares that translation in
# its own document rather than leaving the same constant in two places.
COSMOLOGICAL_CONSTANT = sympy.Symbol("Lambda", real=True)

# The post-Newtonian reading of record 0008, in which general relativity has
# both parameters equal to one. Named so that a parity check quotes a constant
# rather than a literal somebody typed twice.
GAMMA_IN_GENERAL_RELATIVITY = sympy.Integer(1)
BETA_IN_GENERAL_RELATIVITY = sympy.Integer(1)

Components = Sequence[Sequence[sympy.Expr]]


def minkowski() -> sympy.Matrix:
    """Flat space in the signature fixed above, as a matrix."""
    return sympy.diag(*SIGNATURE)


def inverse_metric(metric: sympy.Matrix) -> sympy.Matrix:
    """The inverse metric, which is the only thing that raises an index.

    Record 0008 rules out raising or lowering with anything else. Having one
    function for it means a stage that wanted a different inverse has to say so
    in an import rather than by writing a matrix inverse inline.
    """
    return metric.inv()


def reduced_planck_mass_squared() -> sympy.Expr:
    """The translation a theory written with the reduced Planck mass declares.

    `M^2 = 1 / (8 pi G)`. The record requires the theory's own document to carry
    the declaration; this is the value it declares, so the two cannot be written
    down differently in two places.
    """
    return 1 / COUPLING


def christoffel(
    metric: sympy.Matrix, coordinates: Sequence[sympy.Symbol]
) -> list[list[list[sympy.Expr]]]:
    """The Levi-Civita connection of the metric.

    `Gamma^r_{mn} = 1/2 g^{rs} ( d_m g_{sn} + d_n g_{sm} - d_s g_{mn} )`

    Indexed `[r][m][n]`, upper index first, in the order the formula writes
    them. Record 0005 fixes that the order a tensor's indices are written in is
    the order they mean, and nothing here rearranges them.
    """
    inverse = inverse_metric(metric)
    dimension = len(coordinates)
    half = sympy.Rational(1, 2)
    return [
        [
            [
                sympy.simplify(
                    half
                    * sum(
                        inverse[r, s]
                        * (
                            sympy.diff(metric[s, n], coordinates[m])
                            + sympy.diff(metric[s, m], coordinates[n])
                            - sympy.diff(metric[m, n], coordinates[s])
                        )
                        for s in range(dimension)
                    )
                )
                for n in range(dimension)
            ]
            for m in range(dimension)
        ]
        for r in range(dimension)
    ]


def riemann(
    metric: sympy.Matrix, coordinates: Sequence[sympy.Symbol]
) -> list[list[list[list[sympy.Expr]]]]:
    """The Riemann tensor in the sign convention of record 0008.

    `R^r_{smn} = d_m Gamma^r_{ns} - d_n Gamma^r_{ms}
               + Gamma^r_{ml} Gamma^l_{ns} - Gamma^r_{nl} Gamma^l_{ms}`

    Indexed `[r][s][m][n]`. This is the choice that, together with the Ricci
    contraction below, gives a sphere positive scalar curvature, and
    `tests/rechenstrasse/test_conventions.py` is where that is asserted rather
    than asserted here.
    """
    connection = christoffel(metric, coordinates)
    dimension = len(coordinates)
    return [
        [
            [
                [
                    sympy.simplify(
                        sympy.diff(connection[r][n][s], coordinates[m])
                        - sympy.diff(connection[r][m][s], coordinates[n])
                        + sum(
                            connection[r][m][low] * connection[low][n][s]
                            - connection[r][n][low] * connection[low][m][s]
                            for low in range(dimension)
                        )
                    )
                    for n in range(dimension)
                ]
                for m in range(dimension)
            ]
            for s in range(dimension)
        ]
        for r in range(dimension)
    ]


def ricci(metric: sympy.Matrix, coordinates: Sequence[sympy.Symbol]) -> sympy.Matrix:
    """The Ricci tensor, contracting the first upper index against the third.

    `R_{mn} = R^l_{mln}`. Which contraction is taken is a sign choice as much as
    the Riemann formula is, and it is why this is a function here rather than a
    line somebody writes where they need it.
    """
    curvature = riemann(metric, coordinates)
    dimension = len(coordinates)
    return sympy.Matrix(
        dimension,
        dimension,
        lambda m, n: sympy.simplify(
            sum(curvature[low][m][low][n] for low in range(dimension))
        ),
    )


def ricci_scalar(
    metric: sympy.Matrix, coordinates: Sequence[sympy.Symbol]
) -> sympy.Expr:
    """`R = g^{mn} R_{mn}`, positive on a sphere in this set of conventions."""
    inverse = inverse_metric(metric)
    tensor = ricci(metric, coordinates)
    dimension = len(coordinates)
    return sympy.simplify(
        sum(
            inverse[m, n] * tensor[m, n]
            for m in range(dimension)
            for n in range(dimension)
        )
    )


def einstein_tensor(
    metric: sympy.Matrix, coordinates: Sequence[sympy.Symbol]
) -> sympy.Matrix:
    """`G_{mn} = R_{mn} - 1/2 R g_{mn}`."""
    tensor = ricci(metric, coordinates)
    scalar = ricci_scalar(metric, coordinates)
    return sympy.simplify(tensor - sympy.Rational(1, 2) * scalar * metric)


def field_equations(
    metric: sympy.Matrix,
    coordinates: Sequence[sympy.Symbol],
    stress_energy: sympy.Matrix | None = None,
) -> sympy.Matrix:
    """The field equations as a matrix that vanishes on a solution.

    `G_{mn} + Lambda g_{mn} - 8 pi G T_{mn}`

    The cosmological constant is on the geometry side and carries the symbol
    `COSMOLOGICAL_CONSTANT`. Passing no stress-energy means vacuum, which is the
    case the post-Newtonian and cosmological stages spend most of their time in.
    """
    source = (
        sympy.zeros(len(coordinates), len(coordinates))
        if stress_energy is None
        else stress_energy
    )
    return sympy.simplify(
        einstein_tensor(metric, coordinates)
        + COSMOLOGICAL_CONSTANT * metric
        - COUPLING * source
    )


def _parity(order: Sequence[int]) -> int:
    """The sign of a permutation, from its inversion count."""
    inversions = sum(
        1
        for left in range(len(order))
        for right in range(left + 1, len(order))
        if order[left] > order[right]
    )
    return -1 if inversions % 2 else 1


def symmetrise(
    component: Callable[..., sympy.Expr], indices: Sequence[int]
) -> sympy.Expr:
    """Symmetrise over the given index values, carrying the factorial weight.

    `T_{(mn)} = 1/2 (T_{mn} + T_{nm})`, and `n` indices carry `1/n!`. The weight
    is where the two conventions in use differ, by a factor of two in every
    symmetrised term, and it is the kind of thing everybody knows and nobody
    writes down until two stages written months apart disagree.
    """
    slots = tuple(indices)
    weight = sympy.Rational(1, factorial(len(slots)))
    return sympy.simplify(
        weight * sum(component(*order) for order in permutations(slots))
    )


def antisymmetrise(
    component: Callable[..., sympy.Expr], indices: Sequence[int]
) -> sympy.Expr:
    """Antisymmetrise over the given index values, with the same weight.

    `T_{[mn]} = 1/2 (T_{mn} - T_{nm})`, and `n` indices carry `1/n!`.
    """
    slots = tuple(indices)
    weight = sympy.Rational(1, factorial(len(slots)))
    total = sum(
        _parity(order) * component(*(slots[position] for position in order))
        for order in permutations(range(len(slots)))
    )
    return sympy.simplify(weight * total)


def kinetic_scalar(
    metric: sympy.Matrix,
    coordinates: Sequence[sympy.Symbol],
    field: sympy.Expr,
) -> sympy.Expr:
    """`X = -1/2 g^{mn} (grad_m phi)(grad_n phi)`.

    Positive for a field whose gradient is timelike, which is the homogeneous
    case milestone 6 works in. The other sign is in use elsewhere and produces a
    kinetic term that looks like a ghost, so this is one of the places the
    convention has to be read rather than assumed.
    """
    inverse = inverse_metric(metric)
    dimension = len(coordinates)
    return sympy.simplify(
        -sympy.Rational(1, 2)
        * sum(
            inverse[m, n]
            * sympy.diff(field, coordinates[m])
            * sympy.diff(field, coordinates[n])
            for m in range(dimension)
            for n in range(dimension)
        )
    )


def dalembertian(
    metric: sympy.Matrix,
    coordinates: Sequence[sympy.Symbol],
    field: sympy.Expr,
) -> sympy.Expr:
    """`box phi`, the covariant wave operator on a scalar.

    Written in the divergence form `1/sqrt(-g) d_m ( sqrt(-g) g^{mn} d_n phi )`,
    which is the same thing as `g^{mn} grad_m grad_n phi` and carries no
    Christoffel sign of its own to get wrong.
    """
    inverse = inverse_metric(metric)
    dimension = len(coordinates)
    density = sympy.sqrt(-metric.det())
    return sympy.simplify(
        sum(
            sympy.diff(
                density
                * sum(
                    inverse[m, n] * sympy.diff(field, coordinates[n])
                    for n in range(dimension)
                ),
                coordinates[m],
            )
            for m in range(dimension)
        )
        / density
    )


def horndeski_density(
    metric: sympy.Matrix,
    coordinates: Sequence[sympy.Symbol],
    field: sympy.Expr,
    g2: sympy.Expr,
    g3: sympy.Expr,
    g4: sympy.Expr,
) -> sympy.Expr:
    """The covered Horndeski sector, with the signs record 0008 fixes.

    `G2(phi, X) - G3(phi, X) box phi + G4(phi) R`

    The sign on the middle term is the one that is written differently in
    different papers, and a theory document that meant the other one says so by
    passing the negated function rather than by this module having two modes. A
    potential enters through `G2`.
    """
    return sympy.simplify(
        g2
        - g3 * dalembertian(metric, coordinates, field)
        + g4 * ricci_scalar(metric, coordinates)
    )


def newtonian_potential_equation(
    potential: sympy.Expr,
    coordinates: Sequence[sympy.Symbol],
    density: sympy.Expr,
) -> sympy.Expr:
    """`lap U + 4 pi G rho`, which vanishes where the potential solves its own equation.

    Record 0008 fixes `U` as positive, defined by `lap U = -4 pi G rho`. The
    spatial coordinates are what is passed here, not the four, because the
    Laplacian is the flat one.
    """
    laplacian = sum(sympy.diff(potential, axis, 2) for axis in coordinates)
    return sympy.simplify(laplacian + 4 * sympy.pi * NEWTON_CONSTANT * density)


def post_newtonian_metric(potential: sympy.Expr, gamma: sympy.Expr) -> sympy.Matrix:
    """The first order metric of record 0008's post-Newtonian reading.

    `g_{00} = -1 + 2 U` and `g_{ij} = (1 + 2 gamma U) delta_{ij}`, in the
    reading where general relativity has `gamma = 1`. This is the sign that
    decides whether a parameter comes out with the sign the validation corpus
    expects, which is why it is a function and not three lines in the stage that
    happens to need it first.
    """
    spatial = 1 + 2 * gamma * potential
    return sympy.diag(-1 + 2 * potential, spatial, spatial, spatial)
