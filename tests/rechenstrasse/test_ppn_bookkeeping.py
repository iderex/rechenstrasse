"""The order counting of issue #36, held to the expansion it has to reproduce.

The assertions that matter are the ones that move if a rule is off by one. A
time derivative raising the order and a spatial one not raising it, orders adding
across a product, a sum sitting at its lowest order, and a term crossing the cut
only because a time derivative was counted.

The last group is the components of the post-Newtonian metric for general
relativity, at the orders the standard reading assigns them. Those orders are
written here as a fixture rather than in the module as a table, because a table
in a module is one nobody re-derives. What record 0008 fixes and this suite
therefore does not restate is the first order metric itself, `g_00 = -1 + 2 U`
with `g_ij = (1 + 2 gamma U) delta_ij`; what is asserted here is the order each
of those pieces sits at, which is what the bookkeeping is for.
"""

import sympy

from rechenstrasse.ppn.bookkeeping import SMALL, Bookkeeping, truncate

# The coordinates the fixtures below are written on, with the time coordinate
# named separately because the rule that raises an order is about that one.
TIME = sympy.Symbol("t", real=True)
SPACE = sympy.symbols("x y z", real=True)


def a_bookkeeping() -> Bookkeeping:
    """The standard assignment for the post-Newtonian expansion.

    The Newtonian potential is order two, a velocity is order one, and a
    pressure over a density is order two. Nothing here is derived by this
    module; it is the declaration a caller makes, and it is the place a wrong
    expansion starts.
    """
    potential = sympy.Function("U")
    velocity = sympy.Function("v")
    return Bookkeeping(
        orders={potential: 2, velocity: 1, SMALL: 1},
        time=TIME,
    )


def potential() -> sympy.Expr:
    return sympy.Function("U")(TIME, *SPACE)


def velocity() -> sympy.Expr:
    return sympy.Function("v")(TIME, *SPACE)


def test_a_constant_sits_at_order_zero() -> None:
    counting = a_bookkeeping()
    assert counting.order_of(sympy.Integer(-1)) == 0
    assert counting.order_of(sympy.Rational(1, 2)) == 0


def test_a_declared_quantity_sits_at_the_order_it_was_declared_at() -> None:
    counting = a_bookkeeping()
    assert counting.order_of(potential()) == 2
    assert counting.order_of(velocity()) == 1


def test_an_undeclared_symbol_sits_at_order_zero() -> None:
    """What makes a coupling constant a constant rather than a small quantity."""
    counting = a_bookkeeping()
    assert counting.order_of(sympy.Symbol("G", positive=True)) == 0


def test_orders_add_across_a_product() -> None:
    counting = a_bookkeeping()
    assert counting.order_of(potential() * velocity()) == 3


def test_orders_multiply_through_a_power() -> None:
    counting = a_bookkeeping()
    assert counting.order_of(potential() ** 2) == 4
    assert counting.order_of(velocity() ** 4) == 4


def test_a_sum_sits_at_the_lowest_order_any_of_its_terms_sits_at() -> None:
    """A sum is as large as its largest part, which is its lowest order."""
    counting = a_bookkeeping()
    assert counting.order_of(potential() + velocity()) == 1
    assert counting.order_of(sympy.Integer(1) + potential()) == 0


def test_zero_has_no_order() -> None:
    counting = a_bookkeeping()
    assert counting.order_of(potential() - potential()) is None


def test_a_time_derivative_raises_the_order_by_one() -> None:
    """The rule this module exists for.

    It is the one people carry in their heads, it is off by one in both
    directions, and a term that crossed the cut because it was not counted looks
    exactly like a term that belonged there.
    """
    counting = a_bookkeeping()
    assert counting.order_of(sympy.diff(potential(), TIME)) == 3


def test_a_spatial_derivative_does_not_raise_the_order() -> None:
    """The other half of the same rule, and the near miss for it.

    A rule that raised the order on every derivative would be wrong in a way
    that is invisible in any expression carrying only time derivatives, which is
    most of the ones written down first.
    """
    counting = a_bookkeeping()
    assert counting.order_of(sympy.diff(potential(), SPACE[0])) == 2


def test_a_second_time_derivative_raises_the_order_again() -> None:
    counting = a_bookkeeping()
    assert counting.order_of(sympy.diff(potential(), TIME, 2)) == 4


def test_a_mixed_derivative_counts_only_the_time_slots() -> None:
    counting = a_bookkeeping()
    mixed = sympy.diff(potential(), TIME, SPACE[0], SPACE[1])
    assert counting.order_of(mixed) == 3


def test_a_truncation_keeps_what_is_at_or_below_the_cut() -> None:
    counting = a_bookkeeping()
    expression = sympy.Integer(1) + 2 * potential() + potential() ** 2
    truncated = truncate(counting, expression, cut=2)
    assert sorted(term.order or 0 for term in truncated.kept) == [0, 2]
    assert [term.order for term in truncated.discarded] == [4]


def test_the_order_of_every_retained_term_comes_back_with_it() -> None:
    """The first clause of the done-when, as an assertion.

    Derivable from the code rather than from a comment means the number travels
    with the term, so a reader does not have to recount it to check the cut.
    """
    counting = a_bookkeeping()
    truncated = truncate(counting, sympy.Integer(1) + potential(), cut=2)
    assert {term.order for term in truncated.kept} == {0, 2}
    assert all(term.expression != 0 for term in truncated.kept)


def test_a_discarded_term_is_recorded_rather_than_lost() -> None:
    counting = a_bookkeeping()
    expression = potential() + potential() ** 3
    truncated = truncate(counting, expression, cut=2)
    assert len(truncated.discarded) == 1
    assert truncated.discarded[0].order == 6
    assert truncated.highest_discarded_order() == 6


def test_the_highest_discarded_order_is_the_highest_and_not_the_lowest() -> None:
    """The number a reader needs, and the one it is easy to report instead.

    The lowest says where the truncation started. The highest says how much of
    the expression they are not being shown, and reporting the lowest reads as
    the tighter statement while being the looser one.
    """
    counting = a_bookkeeping()
    expression = potential() + potential() ** 2 + potential() ** 3
    truncated = truncate(counting, expression, cut=2)
    assert sorted(term.order or 0 for term in truncated.discarded) == [4, 6]
    assert truncated.highest_discarded_order() == 6


def test_nothing_discarded_leaves_no_highest_order() -> None:
    counting = a_bookkeeping()
    truncated = truncate(counting, potential(), cut=2)
    assert truncated.discarded == ()
    assert truncated.highest_discarded_order() is None


def test_a_truncation_reassembles_into_the_retained_expression() -> None:
    counting = a_bookkeeping()
    expression = sympy.Integer(1) + 2 * potential() + potential() ** 2
    truncated = truncate(counting, expression, cut=2)
    assert (
        sympy.simplify(truncated.expression() - (sympy.Integer(1) + 2 * potential()))
        == 0
    )


def test_a_sum_is_truncated_term_by_term_rather_than_as_a_whole() -> None:
    """The near miss for the truncation itself.

    A truncation that read the order of the whole sum would see the lowest order
    in it and keep everything, because a small term travelling beside a large
    one is exactly what a sum looks like. That mistake keeps terms rather than
    dropping them, so nothing about the result looks wrong.
    """
    counting = a_bookkeeping()
    expression = sympy.Integer(1) + potential() ** 3
    assert counting.order_of(expression) == 0
    truncated = truncate(counting, expression, cut=2)
    assert len(truncated.kept) == 1
    assert len(truncated.discarded) == 1


def test_a_term_crosses_the_cut_only_because_a_time_derivative_was_counted() -> None:
    """The one-character mistake this whole module is against.

    The term sits at order two by its factors and at order three once the time
    derivative is counted. A bookkeeping that forgot the rule keeps it at a cut
    of two, and the result is a post-Newtonian expression carrying a term from
    the next order with nothing to mark it.
    """
    counting = a_bookkeeping()
    term = sympy.diff(potential(), TIME)
    assert counting.order_of(potential()) == 2
    assert counting.order_of(term) == 3
    truncated = truncate(counting, term, cut=2)
    assert truncated.kept == ()
    assert truncated.highest_discarded_order() == 3


def test_the_metric_components_of_the_general_relativity_expansion() -> None:
    """The third clause of the done-when, on the expansion the pipeline is for.

    In the standard reading the time-time component carries a term at order zero
    and its first correction at order two, the space-space components do the
    same, and the time-space components start at order three because they carry
    a velocity beside a potential. Those three statements are what the order
    counting has to reproduce, and each of them fails on a different mistake:
    the first on a constant read as small, the second on the factor `gamma`
    being read as small rather than as a parameter, and the third on the
    velocity's own order.
    """
    counting = a_bookkeeping()
    gamma = sympy.Symbol("gamma", real=True)

    time_time = -sympy.Integer(1) + 2 * potential()
    assert counting.order_of(time_time) == 0
    assert [term.order for term in truncate(counting, time_time, cut=2).kept] == [0, 2]

    space_space = sympy.Integer(1) + 2 * gamma * potential()
    assert counting.order_of(space_space) == 0
    assert [term.order for term in truncate(counting, space_space, cut=2).kept] == [
        0,
        2,
    ]

    time_space = -4 * gamma * potential() * velocity()
    assert counting.order_of(time_space) == 3
    assert truncate(counting, time_space, cut=2).kept == ()
    assert truncate(counting, time_space, cut=2).highest_discarded_order() == 3


def test_the_expansion_parameter_itself_is_declared_rather_than_special() -> None:
    """`epsilon` is a symbol like any other and carries the order it is given.

    Nothing in the module treats it as a marker to be counted, so an expression
    written with explicit powers of it counts the same way as one written with
    named quantities, and the two cannot disagree.
    """
    counting = a_bookkeeping()
    assert counting.order_of(SMALL**3) == 3
    assert counting.order_of(SMALL * potential()) == 3
