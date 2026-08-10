"""The surface terms the metric variation drops, and what says they were dropped.

Issue #32. A term that is a total derivative contributes nothing to the field
equations, and a boundary term discarded without being named is a defect that
surfaces much later as a factor nobody can find. So the discard is a value the
stage returns rather than a comment beside the code that made it.

What is asserted here, in the order the issue asks for it. That integration by
parts is one named operation and the only place a boundary term is created.
That every derivation carries what it dropped beside the equation it reached.
And that a coefficient which is a function of the field, whose boundary term
therefore has a half that does not go away on its own, is reported with that
half written out rather than reduced to the same sentence a constant coefficient
gets.

What no leg here asserts, said rather than left to be found. Nothing carries
these into a run record: record 0007's provenance block is issue #60 and does
not exist, so what is proved below is that the stage reports them to its caller
and not that an operator ever sees one.
"""

import json
from pathlib import Path

import sympy as sp

from rechenstrasse.document import reader
from rechenstrasse.representation import Action, Lagrangian, Tensor, Term
from rechenstrasse.variation import metric

ROOT = Path(__file__).resolve().parents[2]
THEORIES = ROOT / "theories"

PHI = sp.Symbol("phi")

# The heads whose variation puts a derivative on the variation of the metric,
# which is what an integration by parts is needed for and the only thing that
# creates a boundary term here. Written out so that a head moving into or out of
# this set is a change to this list rather than a number that quietly moves.
#
# Two heads reach it from opposite directions and each drops two divergences. The
# curvature heads put the derivative there through the variation of the
# connection inside `R`, and each of their two divergences is integrated by parts
# twice. The cubic head puts it there through the variation of the connection
# inside `box phi`, and each of its two is integrated by parts once, which is why
# the assumption on them is the weaker of the two.
HEADS_THAT_DROP_A_BOUNDARY_TERM = frozenset(
    {"ricci_scalar", "horndeski_g4", "horndeski_g3"}
)


def action_of(stem: str) -> Action:
    text = (THEORIES / f"{stem}.json").read_text(encoding="utf-8")
    read, refusals = reader.read(text)
    assert refusals == (), f"{stem} was refused by the reader: {refusals}"
    assert read is not None
    return read


def derivation_of(stem: str) -> metric.Derivation:
    produced = metric.derive(action_of(stem))
    assert isinstance(produced, metric.Derivation), produced
    return produced


def heads_of(stem: str) -> list[str]:
    document = json.loads((THEORIES / f"{stem}.json").read_text(encoding="utf-8"))
    return [term["head"] for term in document["lagrangian"]["terms"]]


def test_integration_by_parts_is_one_named_operation_that_says_what_it_dropped() -> (
    None
):
    """Two integrations by parts, two divergences, and each one written out.

    Each divergence carries the scalar in both places the operation put it: once
    under the derivative that was still on the variation of the metric, and once
    under the derivative that came off the scalar. A term naming it in one place
    is one of the two halves written down.
    """
    coefficient = sp.Function("G4")(PHI)
    moved, dropped = metric.integrate_by_parts(coefficient, frozenset())
    assert {shape.kind for shape, _ in moved} == {
        metric.HESSIAN,
        metric.BOX_TIMES_METRIC,
    }
    assert len(dropped) == 2
    for surface in dropped:
        assert surface.divergence.count(str(coefficient)) == 2
        assert surface.assumed == metric.BOUNDARY_ASSUMPTION
        assert surface.around == coefficient
        assert surface.vanishes_by_itself is False


def test_a_boundary_term_reads_back_with_the_assumption_that_dropped_it() -> None:
    """The readable form, which is a divergence and the condition it went under.

    An assumption that lives in a docstring is one the reader of a result never
    sees, so it travels on the term.
    """
    written = str(metric.integrate_by_parts(sp.Function("G4")(PHI), frozenset())[1][0])
    assert written.startswith("grad^l (")
    assert metric.BOUNDARY_ASSUMPTION in written


def test_a_constant_coefficient_drops_a_boundary_term_with_one_half_gone() -> None:
    """General relativity still drops two, and each has lost its second half.

    The half that came off the coefficient is a derivative of a constant, so it
    is zero and is not written. A report that printed it would be describing a
    term the derivation never dropped, which is the same class of untruth as
    hiding one it did.
    """
    dropped = derivation_of("general-relativity-with-a-cosmological-constant")
    assert len(dropped.surface_terms) == 2
    for surface in dropped.surface_terms:
        assert surface.vanishes_by_itself is True
        assert surface.divergence.count("one_over_two_kappa") == 1
        assert "grad_l (one_over_two_kappa)" not in surface.divergence
        assert surface.assumed == metric.BOUNDARY_ASSUMPTION


def test_a_boundary_term_that_does_not_vanish_by_itself_is_written_out() -> None:
    """The case the issue asks for: a boundary term reported rather than dropped.

    `metric-f-of-r-as-a-scalar-tensor-theory` carries a coefficient that is a
    function of the field, so the half of each divergence that came off the
    coefficient is a derivative of something that moves. It is exactly the term
    a reader of a derivation wants to see, because its vanishing is an
    assumption about the boundary rather than an identity.
    """
    dropped = derivation_of("metric-f-of-r-as-a-scalar-tensor-theory")
    assert len(dropped.surface_terms) == 2
    for surface in dropped.surface_terms:
        assert surface.vanishes_by_itself is False
        assert "grad_l (G4_of_phi(phi))" in surface.divergence or (
            "grad^n (G4_of_phi(phi))" in surface.divergence
        )
        assert surface.around == sp.Function("G4_of_phi")(PHI)


def test_every_derivation_in_the_tree_reports_what_it_dropped() -> None:
    """Two boundary terms per term of the action that needs one, and none else.

    The count is derived from the document rather than written down per
    document, so a fifth theory arriving is judged by this leg without an edit
    here.
    """
    stems = sorted(path.stem for path in THEORIES.glob("*.json"))
    assert stems, f"no theory document below {THEORIES}, which is not a pass"
    reached = 0
    for stem in stems:
        produced = metric.derive(action_of(stem))
        if isinstance(produced, metric.NotDerived):
            continue
        reached += 1
        owed = sum(
            2 for head in heads_of(stem) if head in HEADS_THAT_DROP_A_BOUNDARY_TERM
        )
        assert len(produced.surface_terms) == owed, stem
        assert all(
            surface.assumed in metric.BOUNDARY_ASSUMPTIONS
            for surface in produced.surface_terms
        )
    assert reached > 0


def test_a_term_that_integrates_nothing_by_parts_drops_nothing() -> None:
    """`G2` alone reaches the equation without a boundary term, and reports none.

    An empty tuple is the true statement here, and a stage that returned one
    boundary term for every term of the action regardless would pass every leg
    above and fail this one.
    """
    metric_field = Tensor(symbol="g", role="metric", slots=2, symmetries=("symmetric",))
    scalar_field = Tensor(symbol="phi", role="scalar", slots=0, symmetries=())
    template = action_of("brans-dicke")
    handmade = Action(
        schema_version=1,
        metadata=template.metadata,
        manifold=template.manifold,
        fields=(metric_field, scalar_field),
        lagrangian=Lagrangian(
            terms=(
                Term(
                    head="horndeski_g2",
                    coefficient="G2_of_phi_and_X",
                    mentions=(metric_field, scalar_field),
                ),
            )
        ),
        matter=template.matter,
        parameters=(),
        regime=template.regime,
    )
    produced = metric.derive(handmade)
    assert isinstance(produced, metric.Derivation)
    assert produced.surface_terms == ()
    assert produced.equation.terms != ()


def test_the_equation_and_what_was_dropped_are_one_result() -> None:
    """`field_equation` is the same equation with the assumptions taken off it.

    Keeping the convenience is worth one leg: the day the two stop agreeing, a
    caller reading the shorter one is reading an equation this stage did not
    derive.
    """
    stem = "brans-dicke"
    produced = derivation_of(stem)
    assert metric.field_equation(action_of(stem)) == produced.equation
    assert produced.surface_terms != ()


def test_a_document_that_derives_nothing_reports_no_boundary_terms_either() -> None:
    """Nothing was dropped, because nothing was varied.

    Every head the gate covers has a rule, so this is reached with an action
    assembled by hand rather than with a document. No equation exists to have
    assumptions about, and the value that comes back has no place to put a
    boundary term at all. That is the shape rather than an empty tuple beside a
    half derived equation.
    """
    metric_field = Tensor(symbol="g", role="metric", slots=2, symmetries=("symmetric",))
    template = action_of("brans-dicke")
    handmade = Action(
        schema_version=1,
        metadata=template.metadata,
        manifold=template.manifold,
        fields=(metric_field,),
        lagrangian=Lagrangian(
            terms=(
                Term(
                    head="gauss_bonnet",
                    coefficient="alpha",
                    mentions=(metric_field,),
                ),
            )
        ),
        matter=template.matter,
        parameters=(),
        regime=template.regime,
    )
    produced = metric.derive(handmade)
    assert isinstance(produced, metric.NotDerived)


def test_the_cubic_term_drops_two_divergences_under_the_weaker_assumption() -> None:
    """What `horndeski_g3` leaves behind, and why it says less than the rest.

    Issue #114. Its two divergences come from one integration by parts each,
    where the curvature heads need two, so what has to vanish on the boundary is
    the variation of the metric and not also its first derivative. Carrying the
    stronger sentence on them would say the derivation assumed something it did
    not, which is the same class of untruth as hiding a term it dropped.

    Neither of the two is in halves, so neither can lose one, and that is why
    both carry the flag false whatever the coefficient does. The leg holds the
    two assumptions apart rather than asserting membership of a set, because a
    rule that put the stronger sentence on both would pass that.
    """
    dropped = derivation_of("covered-horndeski-sector").surface_terms
    cubic = [
        surface
        for surface in dropped
        if surface.assumed == metric.METRIC_VARIATION_ASSUMPTION
    ]
    curvature = [
        surface for surface in dropped if surface.assumed == metric.BOUNDARY_ASSUMPTION
    ]
    assert len(cubic) == 2
    assert len(curvature) == 2
    assert len(dropped) == 4
    carried = sp.Function("G3_of_phi_and_X")(PHI, metric.KINETIC_SCALAR)
    for surface in cubic:
        assert surface.around == carried
        assert surface.vanishes_by_itself is False
        assert "grad_m (phi)" in surface.divergence or (
            "grad_l (phi)" in surface.divergence
        )
