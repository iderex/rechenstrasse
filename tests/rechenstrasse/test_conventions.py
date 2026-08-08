"""The conventions of record 0008, held to the statements the record makes.

Issue #8. A sign convention is the cheapest available source of a wrong answer
that looks right, so the assertions here are the ones that would move if a sign
flipped: a sphere with positive scalar curvature, a Schwarzschild exterior that
is Ricci flat, a de Sitter background that solves the vacuum equations with a
positive cosmological constant, and a kinetic scalar that is positive for a
timelike gradient. Each of those fails on a flipped sign somewhere in the chain
and none of them fails on a rearrangement that changed nothing.

Two dimensional and four dimensional cases both appear, because the loops in the
module are written over `len(coordinates)` and a suite that only ever passed four
would not notice one of them being wrong.
"""

import sympy

from rechenstrasse import conventions


def test_the_signature_is_the_one_the_record_names() -> None:
    assert conventions.SIGNATURE == (-1, 1, 1, 1)
    assert conventions.SIGNATURE_NAME == "(-, +, +, +)"
    assert conventions.minkowski() == sympy.diag(-1, 1, 1, 1)


def test_a_timelike_interval_is_negative_in_this_signature() -> None:
    """The sentence the record leads with, as an assertion rather than a tuple.

    A reader checking the tree against a textbook page checks this, not the
    ordering of four numbers in a constant.
    """
    flat = conventions.minkowski()
    displacement = sympy.Matrix([1, 0, 0, 0])
    assert (displacement.T * flat * displacement)[0, 0] < 0


def test_flat_space_is_flat() -> None:
    coordinates = sympy.symbols("t x y z", real=True)
    curvature = conventions.riemann(conventions.minkowski(), coordinates)
    assert all(
        curvature[r][s][m][n] == 0
        for r in range(4)
        for s in range(4)
        for m in range(4)
        for n in range(4)
    )


def test_a_sphere_has_positive_scalar_curvature() -> None:
    """The statement record 0008 makes about its own three sign choices.

    A two-sphere of radius `a` has `R = 2 / a^2`. Flip the Riemann sign, or take
    the other Ricci contraction, and this comes out negative. It is the cheapest
    assertion in the tree that pins down the whole chain.
    """
    radius = sympy.Symbol("a", positive=True)
    theta, phi = sympy.symbols("theta phi", real=True)
    metric = sympy.diag(radius**2, radius**2 * sympy.sin(theta) ** 2)
    scalar = conventions.ricci_scalar(metric, (theta, phi))
    assert sympy.simplify(scalar - 2 / radius**2) == 0


def test_the_schwarzschild_exterior_is_ricci_flat() -> None:
    """A vacuum solution of the equations, with no cosmological constant.

    This is the assertion that catches a Christoffel sign, because the Ricci
    tensor of this metric is a cancellation between terms rather than something
    that vanishes term by term.
    """
    mass = sympy.Symbol("M", positive=True)
    t, r, theta, phi = sympy.symbols("t r theta phi", positive=True)
    factor = 1 - 2 * conventions.NEWTON_CONSTANT * mass / r
    metric = sympy.diag(
        -factor,
        1 / factor,
        r**2,
        r**2 * sympy.sin(theta) ** 2,
    )
    tensor = conventions.ricci(metric, (t, r, theta, phi))
    assert sympy.simplify(tensor) == sympy.zeros(4, 4)


def test_de_sitter_solves_the_vacuum_equations_with_a_positive_constant() -> None:
    """The record's other statement about its sign choices.

    Flat-slicing de Sitter with `a = exp(H t)` solves `G_{mn} + Lambda g_{mn} = 0`
    at `Lambda = 3 H^2`, which is positive. On the other sign convention for the
    cosmological constant this would come out at minus that, so the assertion is
    about where `Lambda` sits in the field equations as much as about curvature.
    """
    hubble = sympy.Symbol("H", positive=True)
    t, x, y, z = sympy.symbols("t x y z", real=True)
    scale = sympy.exp(hubble * t)
    metric = sympy.diag(-1, scale**2, scale**2, scale**2)
    equations = conventions.field_equations(metric, (t, x, y, z))
    solved = equations.subs(conventions.COSMOLOGICAL_CONSTANT, 3 * hubble**2)
    assert sympy.simplify(solved) == sympy.zeros(4, 4)


def test_the_coupling_stays_visible_rather_than_being_set_to_one() -> None:
    assert conventions.COUPLING == 8 * sympy.pi * conventions.NEWTON_CONSTANT
    assert conventions.NEWTON_CONSTANT in conventions.COUPLING.free_symbols
    assert conventions.SPEED_OF_LIGHT == 1


def test_the_reduced_planck_mass_translation_is_the_declared_one() -> None:
    assert (
        sympy.simplify(
            conventions.reduced_planck_mass_squared() * conventions.COUPLING - 1
        )
        == 0
    )


def test_symmetrisation_carries_the_factorial_weight() -> None:
    """Rank two by hand, rank three by the definition the weight comes from.

    The rank two case is the one the record writes out. The rank three case is
    what says the weight is `1/n!` rather than a hardcoded half, and it is the
    one that would survive somebody replacing the factorial with a two.
    """
    entries = sympy.Matrix(2, 2, lambda m, n: sympy.Symbol(f"T{m}{n}"))

    def component(m: int, n: int) -> sympy.Expr:
        return entries[m, n]

    assert conventions.symmetrise(component, (0, 1)) == sympy.simplify(
        sympy.Rational(1, 2) * (entries[0, 1] + entries[1, 0])
    )
    assert conventions.antisymmetrise(component, (0, 1)) == sympy.simplify(
        sympy.Rational(1, 2) * (entries[0, 1] - entries[1, 0])
    )

    def rank_three(a: int, b: int, c: int) -> sympy.Expr:
        return sympy.Symbol(f"S{a}{b}{c}")

    six = [
        rank_three(*order)
        for order in ((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0))
    ]
    assert conventions.symmetrise(rank_three, (0, 1, 2)) == sympy.simplify(
        sympy.Rational(1, 6) * sum(six)
    )


def test_an_antisymmetrisation_of_a_symmetric_object_vanishes() -> None:
    symmetric = sympy.Matrix(
        2, 2, lambda m, n: sympy.Symbol(f"U{min(m, n)}{max(m, n)}")
    )

    def component(m: int, n: int) -> sympy.Expr:
        return symmetric[m, n]

    assert conventions.antisymmetrise(component, (0, 1)) == 0


def test_the_kinetic_scalar_is_positive_for_a_timelike_gradient() -> None:
    t, x, y, z = sympy.symbols("t x y z", real=True)
    field = sympy.Symbol("k", positive=True) * t
    value = conventions.kinetic_scalar(conventions.minkowski(), (t, x, y, z), field)
    assert value.is_positive

    spacelike = sympy.Symbol("k", positive=True) * x
    assert conventions.kinetic_scalar(
        conventions.minkowski(), (t, x, y, z), spacelike
    ).is_negative


def test_the_wave_operator_agrees_with_the_flat_one() -> None:
    t, x, y, z = sympy.symbols("t x y z", real=True)
    field = sympy.Function("f")(t, x, y, z)
    box = conventions.dalembertian(conventions.minkowski(), (t, x, y, z), field)
    flat = (
        -sympy.diff(field, t, 2)
        + sympy.diff(field, x, 2)
        + sympy.diff(field, y, 2)
        + sympy.diff(field, z, 2)
    )
    assert sympy.simplify(box - flat) == 0


def test_the_horndeski_sector_carries_the_sign_the_record_fixes() -> None:
    """`G2 - G3 box phi + G4 R`, with the middle term negative.

    Asserted against the three pieces computed separately, so a change to the
    assembly is caught and a change to any one piece is caught by its own test
    above.
    """
    t, x, y, z = sympy.symbols("t x y z", real=True)
    coordinates = (t, x, y, z)
    metric = conventions.minkowski()
    field = sympy.Function("phi")(t)
    g2, g3, g4 = sympy.symbols("G2 G3 G4", real=True)
    density = conventions.horndeski_density(metric, coordinates, field, g2, g3, g4)
    expected = (
        g2
        - g3 * conventions.dalembertian(metric, coordinates, field)
        + g4 * conventions.ricci_scalar(metric, coordinates)
    )
    assert sympy.simplify(density - expected) == 0


def test_the_newtonian_potential_is_positive_outside_a_mass() -> None:
    """`lap U = -4 pi G rho` with `U = G M / r` outside the source.

    The sign is what decides whether the post-Newtonian parameters come out with
    the sign the corpus expects, so it is asserted against a potential a reader
    recognises rather than against the equation rearranged.
    """
    mass = sympy.Symbol("M", positive=True)
    x, y, z = sympy.symbols("x y z", real=True)
    radius = sympy.sqrt(x**2 + y**2 + z**2)
    potential = conventions.NEWTON_CONSTANT * mass / radius
    assert conventions.newtonian_potential_equation(potential, (x, y, z), 0) == 0
    assert potential.subs({x: 1, y: 0, z: 0}).is_positive


def test_the_first_order_metric_is_the_reading_the_record_fixes() -> None:
    potential = sympy.Symbol("U", positive=True)
    gamma = sympy.Symbol("gamma", real=True)
    metric = conventions.post_newtonian_metric(potential, gamma)
    assert metric[0, 0] == -1 + 2 * potential
    for axis in range(1, 4):
        assert metric[axis, axis] == 1 + 2 * gamma * potential
    assert metric.subs(gamma, conventions.GAMMA_IN_GENERAL_RELATIVITY)[1, 1] == (
        1 + 2 * potential
    )


def test_the_first_order_metric_reduces_to_flat_space_with_no_potential() -> None:
    metric = conventions.post_newtonian_metric(sympy.Integer(0), sympy.Symbol("gamma"))
    assert metric == conventions.minkowski()
