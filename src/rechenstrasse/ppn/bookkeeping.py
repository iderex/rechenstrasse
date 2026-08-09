"""The order counting of the post-Newtonian expansion, made explicit.

Issue #36. The expansion is an ordering of small quantities, and almost every
mistake in it is a term kept or dropped at the wrong order. So the order is
computed from the expression rather than remembered, and a truncation says what
it discarded rather than losing it quietly.

What is fixed here. Each quantity that is small carries a declared order in the
bookkeeping parameter, orders add across a product and multiply through a power,
a sum sits at the lowest order any of its terms sits at, and a derivative with
respect to the time coordinate raises the order by one while a spatial one does
not. That last rule is the one this module exists for: it is the rule people
carry in their heads, it is off by one in both directions, and a term that
crossed the cut because a time derivative was not counted looks exactly like a
term that belonged there.

The record of discarded terms is part of what a truncation returns rather than
something a debug flag prints. Somebody checking a derivation wants the highest
order that was dropped, because that is the number that says whether the result
is usable at the precision they care about, and a truncation that returns only
what it kept cannot answer.

Everything here is exact. There is no float literal in this module and there may
not be one, which is record 0006's boundary and the rule
`no-float-above-the-boundary` refusing it. The bookkeeping parameter is a symbol
and is never given a value; nothing here evaluates anything.

What this is written on. The internal representation of record 0005 is an
expression over tensor terms with abstract indices and does not exist yet, so
the functions below take the expressions the tree can carry today, which is what
`rechenstrasse.conventions` already does for the same reason. What issue #36
asks for is that the order of a retained term be derivable from the code rather
than from a comment, and that is true of these definitions whether the thing
they are called with is a component expression or an abstract-index term.

What this does not do. It does not decide which order a quantity sits at. That
is a declaration the caller makes, in `Bookkeeping.orders`, and it is the place
a wrong expansion starts. Nothing here can check a declaration against physics,
and the standard assignment for the post-Newtonian metric is written in the
suite as a fixture rather than here as a constant, because a table in a module
is a table nobody re-derives.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

import sympy

# The bookkeeping parameter. One symbol, positive, never given a value. An order
# is an exponent of this and nothing else, so "order 2" has one meaning in this
# tree.
SMALL: Final = sympy.Symbol("epsilon", positive=True)

# What the order of the zero expression is. Zero sits at every order and at
# none, and the two readings differ in what a truncation does with it, so it is
# named rather than answered with a number.
ZERO_HAS_NO_ORDER: Final = None


@dataclass(frozen=True)
class Bookkeeping:
    """Which quantities are small, how small, and which coordinate is time.

    `orders` maps a symbol, or the head of a function of the coordinates, onto
    the order it sits at. A symbol that is not in it sits at order zero, which
    is what makes a constant a constant.

    `time` is the coordinate a derivative with respect to raises the order by
    one. It is a field rather than a convention read off the first coordinate,
    because a stage that passed its coordinates in another order would then be
    counting the wrong derivative and nothing would say so.
    """

    orders: Mapping[sympy.Basic, int]
    time: sympy.Symbol

    def order_of(self, expression: sympy.Expr) -> int | None:
        """The order this expression sits at, or nothing where it is zero.

        The lowest order any of its terms sits at, which is what an expansion
        means by the order of a sum: a sum is as large as its largest part.
        """
        expanded = sympy.expand(expression)
        if expanded == 0:
            return ZERO_HAS_NO_ORDER
        orders = [self._order_of_term(term) for term in sympy.Add.make_args(expanded)]
        present = [order for order in orders if order is not None]
        if not present:
            return ZERO_HAS_NO_ORDER
        return min(present)

    def _order_of_term(self, term: sympy.Expr) -> int | None:
        if term == 0:
            return ZERO_HAS_NO_ORDER
        if isinstance(term, sympy.Mul):
            parts = [self._order_of_term(factor) for factor in term.args]
            if any(part is None for part in parts):
                return ZERO_HAS_NO_ORDER
            return sum(part for part in parts if part is not None)
        if isinstance(term, sympy.Pow):
            base, exponent = term.args
            inner = self._order_of_term(base)
            if inner is None or not exponent.is_Integer:
                return inner
            return inner * int(exponent)
        if isinstance(term, sympy.Derivative):
            inner = self._order_of_term(term.expr)
            if inner is None:
                return ZERO_HAS_NO_ORDER
            return inner + self._time_derivatives(term)
        if isinstance(term, sympy.Add):
            return self.order_of(term)
        if term.is_number:
            return 0
        return self._declared(term)

    def _declared(self, term: sympy.Expr) -> int:
        """The order declared for a symbol, or for the head of an applied function.

        A function of the coordinates is read by its head, so `U(t, x, y, z)`
        and `U(t, x)` are the same quantity at the same order and a stage that
        writes one of them does not have to declare both.
        """
        if term in self.orders:
            return self.orders[term]
        head = term.func if term.args else term
        return self.orders.get(head, 0)

    def _time_derivatives(self, term: sympy.Derivative) -> int:
        """How many of this derivative's slots are the time coordinate.

        Counted with multiplicity, because the rule is per derivative taken and
        a second time derivative raises the order again.
        """
        taken = 0
        for variable, count in term.variable_count:
            if variable == self.time:
                taken += int(count)
        return taken


@dataclass(frozen=True)
class Term:
    """One term of a sum, and the order it was found to sit at."""

    expression: sympy.Expr
    order: int | None


@dataclass(frozen=True)
class Truncation:
    """What a truncation kept, what it discarded, and how far up it discarded.

    `discarded` is not a debug channel. A reader of a derivation wants to see
    which terms were assumed to be negligible and at what order, and a
    truncation that returned only `kept` would be telling them what is there
    without telling them what is not.
    """

    cut: int
    kept: tuple[Term, ...]
    discarded: tuple[Term, ...]

    def expression(self) -> sympy.Expr:
        """The retained part, as one expression."""
        total: sympy.Expr = sympy.Integer(0)
        for term in self.kept:
            total = total + term.expression
        return total

    def highest_discarded_order(self) -> int | None:
        """The highest order that was dropped, or nothing where nothing was.

        This is the number a reader needs, and it is the highest rather than the
        lowest: the lowest tells them where the truncation started, and the
        highest tells them how much of the expression they are not being shown.
        """
        orders = [term.order for term in self.discarded if term.order is not None]
        return max(orders) if orders else None


def truncate(bookkeeping: Bookkeeping, expression: sympy.Expr, cut: int) -> Truncation:
    """Keep every term at or below `cut`, and record every term above it.

    Term by term over the expanded sum, because the order of a sum is the lowest
    of its parts and truncating a sum as a whole would keep terms it should have
    dropped whenever one small term travelled with a large one.

    A term of no order, which is a term that is zero, is neither kept nor
    discarded. It carries nothing either way and reporting it as discarded would
    put noise into the one list a reader is meant to read closely.
    """
    kept: list[Term] = []
    discarded: list[Term] = []
    for part in sympy.Add.make_args(sympy.expand(expression)):
        order = bookkeeping.order_of(part)
        if order is None:
            continue
        (kept if order <= cut else discarded).append(Term(expression=part, order=order))
    return Truncation(cut=cut, kept=tuple(kept), discarded=tuple(discarded))
