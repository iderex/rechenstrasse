"""The metric variation, against the field equations somebody else published.

Issue #30. What makes this stage checkable is not that its output looks like a
field equation. It is that for the theories whose field equations are in the
literature, the expression this pipeline derives and the expression somebody
published are the same expression, and the comparison is subtraction to zero
rather than a reader agreeing that two printed lines match.

Three theories in the tree have a published metric equation, and all three are
compared here. General relativity with a cosmological constant and metric f(R)
are the two issue #30 names. Brans-Dicke is the third and is compared for a
reason the other two do not give: it is the only one of them whose equation
carries the gradient pair and the scalar-dependent coefficient at the same time,
so a derivation that lost the kinetic term or misplaced a power of the field
passes the first two and fails it.

The cubic Horndeski term is issue #114 and is compared at the end of the file,
against a source of its own rather than against any of those three, because none
of them carries that term. Two things sit around that comparison. What has to be
translated between the two conventions is written where the source is named, and
a second comparison from a direction the source does not give runs beside it: the
cubic term at a coefficient linear in the field is a quadratic term, and the two
routes to its equation share nothing but have to agree.

What each comparison has to supply, and why it is supplied here rather than read
out of a document. Schema version 1 says which terms a theory carries and which
symbol stands in front of each, and it has no key for what those symbols mean.
The reading of a symbol is therefore written beside the comparison it is used
in, together with the source it comes from, which is record 0008's direction of
travel for a published value applied to a published expression.

The normalisation, stated once. This stage produces `E_mn`, and the field
equation is `E_mn = 1/2 T_mn`. Every published equation below is written with the
stress-energy tensor on the right at the coupling its source uses, so each
expected form here is that published equation divided by twice the coupling. The
division is written into the expected form rather than performed on the derived
one, so nothing is done to the thing under test to make it agree.

Every comparison here has a near miss under it, and each one is a single
character somebody would actually get wrong: the sign of the piece the connection
variation leaves behind, the factor of one half in front of the trace term, the
sign of the kinetic contribution, the sign on the piece carrying the box of the
field, the factor of two on the structure only the cubic term produces, and the
trace piece losing its contraction. Each is asserted to fail the comparison the
leg above it passes, which is what stops those legs from being ways of writing
`True`.
"""

import json
from pathlib import Path

import pytest
import sympy as sp

from rechenstrasse.admissibility import gate
from rechenstrasse.document import reader
from rechenstrasse.representation import Action, Lagrangian, Parameter, Tensor, Term
from rechenstrasse.variation import metric

ROOT = Path(__file__).resolve().parents[2]
THEORIES = ROOT / "theories"

# The two symbols record 0008 fixes that a reading below writes with, named here
# so that no leg spells one of them twice.
PHI = sp.Symbol("phi")
CURVATURE = metric.CURVATURE_SCALAR
KINETIC = metric.KINETIC_SCALAR
COUPLING = metric.COUPLING


def document(stem: str) -> dict[str, object]:
    return dict(json.loads((THEORIES / f"{stem}.json").read_text(encoding="utf-8")))


def action_of(stem: str) -> Action:
    """The action one theory document reads as, with nothing refused on the way."""
    text = (THEORIES / f"{stem}.json").read_text(encoding="utf-8")
    read, refusals = reader.read(text)
    assert refusals == (), f"{stem} was refused by the reader: {refusals}"
    assert read is not None
    return read


def derived(stem: str) -> metric.FieldEquation:
    produced = metric.field_equation(action_of(stem))
    assert isinstance(produced, metric.FieldEquation), produced
    return produced


def citation_of(stem: str) -> str:
    metadata = document(stem)["metadata"]
    assert isinstance(metadata, dict)
    return str(metadata["citation"])


def equation(*terms: tuple[metric.Structure, sp.Expr]) -> metric.FieldEquation:
    """An expected form, assembled the same way a derived one is.

    The constants are the ones the comparison is made in, and every expected
    form below is compared against a derived equation by `minus`, which reads
    the constants of the derived side rather than of this one.
    """
    return metric._assemble(list(terms), frozenset())


def agree(left: metric.FieldEquation, right: metric.FieldEquation) -> bool:
    return left.minus(right).is_zero()


def scaled(by: sp.Expr, of: metric.FieldEquation) -> metric.FieldEquation:
    """One equation times a number, which is how a normalisation is translated."""
    return metric._assemble(
        [(shape, by * standing) for shape, standing in of.terms], of.constants
    )


def one_term_action(head: str, coefficient: str, *, carries: str = "") -> Action:
    """An action carrying a single term, so one contribution is read on its own.

    Assembled here rather than put in `theories/`, because the tree holds the
    theories somebody might want the parameters of and this is a term under a
    microscope. `carries` names one parameter the theory declares, which is what
    makes a symbol constant to the derivation.
    """
    template = action_of("covered-horndeski-sector")
    metric_field = Tensor(symbol="g", role="metric", slots=2, symmetries=("symmetric",))
    scalar_field = Tensor(symbol="phi", role="scalar", slots=0, symmetries=())
    parameters = (
        (Parameter(symbol=carries, minimum=None, maximum=None, claimed_by="the leg"),)
        if carries
        else ()
    )
    return Action(
        schema_version=1,
        metadata=template.metadata,
        manifold=template.manifold,
        fields=(metric_field, scalar_field),
        lagrangian=Lagrangian(
            terms=(
                Term(
                    head=head,
                    coefficient=coefficient,
                    mentions=(metric_field, scalar_field),
                ),
            )
        ),
        matter=template.matter,
        parameters=parameters,
        regime=template.regime,
    )


def contribution_of(head: str, coefficient: str) -> metric.FieldEquation:
    produced = metric.field_equation(one_term_action(head, coefficient))
    assert isinstance(produced, metric.FieldEquation), produced
    return produced


def by_the_field(expression: sp.Expr) -> sp.Expr:
    return sp.Derivative(expression, PHI).doit()


def by_the_kinetic(expression: sp.Expr) -> sp.Expr:
    return sp.Derivative(expression, KINETIC).doit()


def test_every_covered_head_is_varied() -> None:
    """Every head the gate covers has a rule here, and no rule covers no head.

    This is what holds the accepted surface and the derived surface together. A
    head widened into the covered class without a variation rule would otherwise
    arrive here as a term nothing varies, and the equation for a document
    carrying it would be missing a term rather than absent.
    """
    assert set(gate.COVERED_HEADS) == set(metric.RULES)


def test_general_relativity_reproduces_the_published_field_equations() -> None:
    """`G_mn + Lambda g_mn = 8 pi G T_mn`, which is record 0008's own equation.

    The reading is the one the document's coefficient names: the constant in
    front of the curvature scalar is `1 / (16 pi G)`. The cosmological constant
    head carries record 0008's normalisation itself, so nothing is read for it.
    """
    stem = "general-relativity-with-a-cosmological-constant"
    citation = "A. Einstein, Sitzungsberichte der Preussischen Akademie der "
    citation += "Wissenschaften (Berlin), 142 (1917)"
    assert citation == citation_of(stem)

    lam = sp.Symbol("Lambda")
    reading = ({sp.Symbol("one_over_two_kappa"): 1 / (2 * COUPLING)},)
    published = equation(
        (metric.Structure(metric.RICCI), 1 / (2 * COUPLING)),
        (
            metric.Structure(metric.METRIC),
            (-sp.Rational(1, 2) * CURVATURE + lam) / (2 * COUPLING),
        ),
    )
    assert agree(metric.substituting(derived(stem), reading), published)


def test_metric_f_of_r_reproduces_the_published_fourth_order_equation() -> None:
    """`f' R_mn - 1/2 f g_mn + (g_mn box - grad_m grad_n) f' = 8 pi G T_mn`.

    The document writes metric f(R) in the scalar-tensor form the pipeline can
    take, so the reading is that equivalence: the coefficient of the curvature
    scalar is `phi / (16 pi G)`, the other term is the potential at the same
    normalisation, and the potential and the field are then written in `f` and
    its derivative. The second derivatives of `f'` are what makes this equation
    fourth order, and they are the ones the connection variation leaves behind.
    """
    stem = "metric-f-of-r-as-a-scalar-tensor-theory"
    citation = "T. P. Sotiriou and V. Faraoni, Reviews of Modern Physics 82, 451 (2010)"
    assert citation == citation_of(stem)

    f = sp.Function("f")
    potential = sp.Function("V")
    of_phi, of_kinetic = sp.symbols("of_phi of_kinetic")
    derivative_of_f = sp.Derivative(f(CURVATURE), CURVATURE)
    reading = (
        {
            sp.Function("G4_of_phi"): sp.Lambda(of_phi, of_phi / (2 * COUPLING)),
            sp.Function("G2_of_phi"): sp.Lambda(
                (of_phi, of_kinetic), -potential(of_phi) / (2 * COUPLING)
            ),
        },
        {potential(PHI): CURVATURE * derivative_of_f - f(CURVATURE)},
        {PHI: derivative_of_f},
    )
    published = equation(
        (metric.Structure(metric.RICCI), derivative_of_f / (2 * COUPLING)),
        (
            metric.Structure(metric.METRIC),
            -sp.Rational(1, 2) * f(CURVATURE) / (2 * COUPLING),
        ),
        (
            metric.Structure(metric.BOX_TIMES_METRIC, derivative_of_f),
            1 / (2 * COUPLING),
        ),
        (metric.Structure(metric.HESSIAN, derivative_of_f), -1 / (2 * COUPLING)),
    )
    assert agree(metric.substituting(derived(stem), reading), published)


def test_brans_dicke_reproduces_the_published_field_equations() -> None:
    """The Jordan frame equation, at the coupling Brans and Dicke wrote it in.

    Their action is `(1 / 16 pi) integral sqrt(-g) [ phi R - (omega / phi)
    grad^m phi grad_m phi ]`, which is the reading below, and the equation is

        G_mn = (8 pi / phi) T_mn
             + (omega / phi^2) ( grad_m phi grad_n phi
                                 - 1/2 g_mn grad^l phi grad_l phi )
             + (1 / phi) ( grad_m grad_n phi - g_mn box phi )

    The trace piece is written with the kinetic scalar rather than with the
    contraction, because record 0008 defines `X` as minus one half of it and
    this module holds no metric to contract with. That substitution is an
    identity of the definition and not a step in the derivation.
    """
    stem = "brans-dicke"
    citation = "C. Brans and R. H. Dicke, Physical Review 124, 925 (1961)"
    assert citation == citation_of(stem)

    omega = sp.Symbol("omega")
    of_phi, of_kinetic = sp.symbols("of_phi of_kinetic")
    reading = (
        {
            sp.Function("G4_of_phi"): sp.Lambda(of_phi, of_phi / (16 * sp.pi)),
            sp.Function("G2_of_phi_and_X"): sp.Lambda(
                (of_phi, of_kinetic), omega * of_kinetic / (8 * sp.pi * of_phi)
            ),
        },
    )
    # The published equation above, brought to the side `E_mn` is on: multiplied
    # by `phi / (16 pi)` and with the stress-energy term dropped, since `E_mn`
    # is the gravitational side alone.
    published = equation(
        (metric.Structure(metric.RICCI), PHI / (16 * sp.pi)),
        (
            metric.Structure(metric.METRIC),
            -PHI * CURVATURE / (32 * sp.pi) - omega * KINETIC / (16 * sp.pi * PHI),
        ),
        (
            metric.Structure(metric.GRADIENT_PAIR),
            -omega / (16 * sp.pi * PHI),
        ),
        (metric.Structure(metric.BOX_TIMES_METRIC, PHI), 1 / (16 * sp.pi)),
        (metric.Structure(metric.HESSIAN, PHI), -1 / (16 * sp.pi)),
    )
    assert agree(metric.substituting(derived(stem), reading), published)


def test_a_constant_coefficient_leaves_no_second_derivative_behind() -> None:
    """General relativity is second order, and that is a result rather than a rule.

    The same rule varies `ricci_scalar` and `horndeski_g4`. What separates them
    is that the first carries a constant, so the two terms the connection
    variation leaves behind are derivatives of a constant and vanish. Nothing in
    the rule special-cases the Einstein-Hilbert term.
    """
    equations = derived("general-relativity-with-a-cosmological-constant")
    kinds = {shape.kind for shape, _ in equations.terms}
    assert metric.HESSIAN not in kinds
    assert metric.BOX_TIMES_METRIC not in kinds
    assert kinds == {metric.RICCI, metric.METRIC}


def test_a_parameter_the_document_declares_is_a_constant_of_the_derivation() -> None:
    """What a theory holds constant is read off its document, not recognised.

    None of the three published readings above puts a declared parameter inside
    a second derivative, so without this leg the parameters could stop counting
    as constants and every comparison would still pass. The day one of them does
    sit inside a derivative, a parameter left out here would be held as
    something that varies, and the derivative of a constant would survive into
    the equation.
    """
    of_general_relativity = metric.constants_of(
        action_of("general-relativity-with-a-cosmological-constant")
    )
    assert of_general_relativity == {
        sp.Symbol("Lambda"),
        sp.Symbol("one_over_two_kappa"),
        metric.NEWTON_CONSTANT,
    }

    omega = sp.Symbol("omega")
    of_brans_dicke = metric.constants_of(action_of("brans-dicke"))
    assert of_brans_dicke == {omega, metric.NEWTON_CONSTANT}
    assert metric._derivative_of(
        metric.HESSIAN, omega * PHI, sp.Integer(1), of_brans_dicke
    ) == [(metric.Structure(metric.HESSIAN, PHI), omega)]


def test_an_equation_reads_back_with_every_structure_named() -> None:
    """The readable form, which is what a person meets before any exporter exists.

    Each of the five structures prints as the expression it stands for rather
    than as the name of a kind, because `hessian` on a page tells a reader
    nothing about which scalar was differentiated.
    """
    written = str(
        equation(
            (metric.Structure(metric.RICCI), sp.Integer(1)),
            (metric.Structure(metric.METRIC), CURVATURE),
            (metric.Structure(metric.GRADIENT_PAIR), sp.Integer(2)),
            (metric.Structure(metric.HESSIAN, PHI), sp.Integer(3)),
            (metric.Structure(metric.BOX_TIMES_METRIC, PHI), sp.Integer(4)),
        )
    )
    assert "R_mn" in written
    assert "g_mn" in written
    assert "grad_m phi grad_n phi" in written
    assert "grad_m grad_n (phi)" in written
    assert "g_mn box (phi)" in written


def test_a_structure_the_equation_does_not_carry_stands_at_zero() -> None:
    """Reading a coefficient off an equation, and what absence means.

    Zero rather than an error, because a comparison against a published form
    asks for every structure that form carries and a structure the derivation
    did not produce is one whose coefficient came out zero.
    """
    equations = derived("general-relativity-with-a-cosmological-constant")
    assert equations.coefficient(metric.Structure(metric.RICCI)) == sp.Symbol(
        "one_over_two_kappa"
    )
    assert equations.coefficient(metric.Structure(metric.HESSIAN, PHI)) == 0


def test_a_head_with_no_rule_and_no_entry_produces_no_equation() -> None:
    """The arm that catches a head widened into the gate with nothing to vary it.

    No document in the tree reaches it, because the gate refuses every head that
    is not covered and the leg above holds the covered set against the two sets
    here. It is reached with an action assembled by hand, because the day it
    stops being unreachable is the day somebody widens the covered class, and an
    arm nothing has ever executed is not one to find out about then.
    """
    metric_field = Tensor(symbol="g", role="metric", slots=2, symmetries=("symmetric",))
    template = action_of("general-relativity-with-a-cosmological-constant")
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
    produced = metric.field_equation(handmade)
    assert isinstance(produced, metric.NotDerived)
    assert "no variation rule for that head" in produced.reasons[0]


def test_linearity_takes_a_constant_out_of_a_second_derivative() -> None:
    """`grad_m grad_n (phi / c)` and `(1 / c) grad_m grad_n phi` are one structure.

    Without this the comparison against a published equation would be a
    comparison of spellings, since a reading that divides by the coupling puts
    the constant inside the derivative and every published form writes it
    outside.
    """
    constant = sp.Symbol("c")
    produced = metric._derivative_of(
        metric.HESSIAN, PHI / constant, sp.Integer(1), frozenset({constant})
    )
    assert produced == [(metric.Structure(metric.HESSIAN, PHI), 1 / constant)]

    # And a symbol the document did not declare constant stays inside, because
    # the derivative of it is not zero and pulling it out would be wrong.
    stays = metric._derivative_of(
        metric.HESSIAN, PHI / constant, sp.Integer(1), frozenset()
    )
    assert stays == [(metric.Structure(metric.HESSIAN, PHI / constant), sp.Integer(1))]


def test_every_theory_document_in_the_tree_is_varied() -> None:
    """Every document reaches an equation, and none is silently skipped."""
    stems = sorted(path.stem for path in THEORIES.glob("*.json"))
    assert stems, f"no theory document below {THEORIES}, which is not a pass"
    for stem in stems:
        produced = metric.field_equation(action_of(stem))
        assert isinstance(produced, metric.FieldEquation), (stem, produced)
        assert produced.terms != ()


def test_the_covered_horndeski_document_yields_a_field_equation() -> None:
    """The document that was the one gap, and the structures it now reaches.

    Issue #114. While the cubic head had no rule, this whole document produced
    nothing rather than three terms out of four, because a field equation missing
    one term of the action is wrong in the way that looks right. It is also the
    entry record 0011 chose to exercise the part of the covered class the other
    three documents do not, so it is the one whose absence cost the most.

    The two structures asserted here are the ones only the cubic term produces.
    """
    produced = derived("covered-horndeski-sector")
    kinds = {shape.kind for shape, _ in produced.terms}
    assert metric.MIXED_GRADIENT_PAIR in kinds
    assert kinds == {
        metric.RICCI,
        metric.METRIC,
        metric.GRADIENT_PAIR,
        metric.MIXED_GRADIENT_PAIR,
        metric.HESSIAN,
        metric.BOX_TIMES_METRIC,
    }
    written = str(produced)
    assert "grad_(m (X) grad_n) phi" in written
    assert "box(phi)" in written


def test_a_term_that_resolved_to_no_scalar_field_produces_no_equation() -> None:
    """A term the reader would never have built, and what this stage does with it.

    `undeclared-field` refuses such a document before an action exists, so this
    action is assembled by hand. The leg is here because the alternative to
    saying so is a coefficient built on a scalar symbol nobody declared, which
    would derive an equation about a field the document never carried.
    """
    metric_field = Tensor(symbol="g", role="metric", slots=2, symmetries=("symmetric",))
    handmade = Action(
        schema_version=1,
        metadata=action_of("brans-dicke").metadata,
        manifold=action_of("brans-dicke").manifold,
        fields=(metric_field,),
        lagrangian=Lagrangian(
            terms=(
                Term(
                    head="horndeski_g4",
                    coefficient="G4_of_phi",
                    mentions=(metric_field,),
                ),
            )
        ),
        matter=action_of("brans-dicke").matter,
        parameters=(),
        regime=action_of("brans-dicke").regime,
    )
    produced = metric.field_equation(handmade)
    assert isinstance(produced, metric.NotDerived)
    assert "resolved to no scalar field" in produced.reasons[0]


@pytest.mark.parametrize(
    "edit",
    [
        # The sign of the piece the connection variation leaves behind, which is
        # the one that makes metric f(R) fourth order.
        metric.HESSIAN,
        # The factor of one half in front of the trace term.
        metric.METRIC,
    ],
)
def test_a_wrong_character_in_the_expected_form_is_caught(edit: str) -> None:
    """The comparison bites, which is what stops the legs above being tautologies.

    Each expected form is rebuilt with one coefficient altered by the smallest
    edit somebody would actually make, and the comparison that passed above has
    to fail. A comparison that could not fail proves nothing about the
    derivation it is comparing.
    """
    stem = "metric-f-of-r-as-a-scalar-tensor-theory"
    f = sp.Function("f")
    potential = sp.Function("V")
    of_phi, of_kinetic = sp.symbols("of_phi of_kinetic")
    derivative_of_f = sp.Derivative(f(CURVATURE), CURVATURE)
    reading = (
        {
            sp.Function("G4_of_phi"): sp.Lambda(of_phi, of_phi / (2 * COUPLING)),
            sp.Function("G2_of_phi"): sp.Lambda(
                (of_phi, of_kinetic), -potential(of_phi) / (2 * COUPLING)
            ),
        },
        {potential(PHI): CURVATURE * derivative_of_f - f(CURVATURE)},
        {PHI: derivative_of_f},
    )
    trace = -sp.Rational(1, 2) * f(CURVATURE) / (2 * COUPLING)
    hessian = -1 / (2 * COUPLING)
    if edit == metric.HESSIAN:
        hessian = -hessian
    else:
        trace = trace * 2
    near_miss = equation(
        (metric.Structure(metric.RICCI), derivative_of_f / (2 * COUPLING)),
        (metric.Structure(metric.METRIC), trace),
        (
            metric.Structure(metric.BOX_TIMES_METRIC, derivative_of_f),
            1 / (2 * COUPLING),
        ),
        (metric.Structure(metric.HESSIAN, derivative_of_f), hessian),
    )
    assert not agree(metric.substituting(derived(stem), reading), near_miss), edit


def test_the_kinetic_contribution_is_not_lost_by_a_sign() -> None:
    """The third near miss, on the term only Brans-Dicke among the three carries.

    Metric f(R) has no kinetic dependence at all, so the two legs above would
    pass a derivation that dropped the gradient pair entirely. This one would
    not.
    """
    omega = sp.Symbol("omega")
    of_phi, of_kinetic = sp.symbols("of_phi of_kinetic")
    reading = (
        {
            sp.Function("G4_of_phi"): sp.Lambda(of_phi, of_phi / (16 * sp.pi)),
            sp.Function("G2_of_phi_and_X"): sp.Lambda(
                (of_phi, of_kinetic), omega * of_kinetic / (8 * sp.pi * of_phi)
            ),
        },
    )
    near_miss = equation(
        (metric.Structure(metric.RICCI), PHI / (16 * sp.pi)),
        (
            metric.Structure(metric.METRIC),
            -PHI * CURVATURE / (32 * sp.pi) - omega * KINETIC / (16 * sp.pi * PHI),
        ),
        (metric.Structure(metric.GRADIENT_PAIR), omega / (16 * sp.pi * PHI)),
        (metric.Structure(metric.BOX_TIMES_METRIC, PHI), 1 / (16 * sp.pi)),
        (metric.Structure(metric.HESSIAN, PHI), -1 / (16 * sp.pi)),
    )
    assert not agree(metric.substituting(derived("brans-dicke"), reading), near_miss)


# The source the cubic contribution is compared against, and everything that has
# to be translated on the way there. Its action is
#
#     S = (1 / kappa) integral d^4x sqrt(-g) [ R + X - V(phi) + G2 + G3 box phi ]
#
# with `kappa = 16 pi G`, and it defines `X` as record 0008 defines it, so the
# kinetic scalar crosses over unchanged. Two things do not.
#
# The sign of the cubic term. That action carries `+G3 box phi` where record 0008
# fixes `-G3 box phi`, so the coefficient this document writes reaches the source
# with its sign flipped, and the legs below flip it where they use it rather than
# folding the flip into a written-out expression.
#
# The normalisation of the equation. `kappa` multiplies the curvature term and
# the rest of the Lagrangian alike, so it cancels out of the field equation and
# the source right hand side should be minus what this stage derives. Taken with
# the action printed beside it, that equation is twice that, and the same factor
# stands on the pure kinetic term and on the whole quadratic sector, which are
# not the sector under test. So the first leg fixes that one number where the
# cubic term has no part in it, and the second leg then asks the cubic sector to
# agree with nothing left to move.
SOURCE = "P. Figueras and T. França, Classical and Quantum Gravity 37, 225009 (2020)"

# What that one number is, and the direction it points. `E_mn` sits on the other
# side of the equation from that right hand side, which is the minus, and the
# half is the factor above.
TO_THE_DERIVED_SIDE = -sp.Rational(1, 2)


def test_the_source_normalisation_is_fixed_where_the_cubic_term_has_no_part() -> None:
    """The quadratic sector of that equation, against what this stage derives.

    This leg is not about the cubic term at all. It is what makes the next one
    mean something: the factor between that source and this stage is measured
    here, on a sector the cubic rule does not touch, and the second half of the
    leg is the same comparison with the factor taken at its face value, which
    fails.
    """
    quadratic = sp.Function("G2_of_phi_and_X")(PHI, KINETIC)
    right_hand_side = equation(
        (metric.Structure(metric.METRIC), quadratic),
        (metric.Structure(metric.GRADIENT_PAIR), by_the_kinetic(quadratic)),
    )
    produced = contribution_of("horndeski_g2", "G2_of_phi_and_X")
    assert agree(produced, scaled(TO_THE_DERIVED_SIDE, right_hand_side)), SOURCE
    assert not agree(produced, scaled(sp.Integer(-1), right_hand_side))


def test_the_cubic_term_matches_the_published_covariant_form() -> None:
    """The contribution of `horndeski_g3`, against the equation somebody published.

    Issue #114. That right hand side carries the cubic term in three places, and
    each is written below in the structures of this module. The contraction
    identities that put them there are identities of record 0008's definition of
    `X` rather than steps in a derivation:

        grad_m X = - grad^a phi grad_m grad_a phi

    so the source's `(grad^a phi)(grad_(m phi) grad_n) grad_a phi` is minus the
    mixed gradient pair, and its `(grad^a phi)(grad^b phi) grad_a grad_b phi` is
    minus the contraction of the two gradients.

    The comparison is subtraction to zero with no tolerance in it, and the
    coefficient reaching the source is the one this document carries with its
    sign flipped, which is the whole of the translation between the two
    conventions for the cubic term.
    """
    carried = sp.Function("G3_of_phi_and_X")(PHI, KINETIC)
    at_the_source = -carried
    right_hand_side = equation(
        (
            metric.Structure(metric.METRIC),
            2 * KINETIC * by_the_field(at_the_source)
            - by_the_kinetic(at_the_source) * metric.GRADIENT_PRODUCT(KINETIC, PHI),
        ),
        (
            metric.Structure(metric.GRADIENT_PAIR),
            2 * by_the_field(at_the_source)
            + by_the_kinetic(at_the_source) * metric.BOX(PHI),
        ),
        (
            metric.Structure(metric.MIXED_GRADIENT_PAIR, KINETIC),
            2 * by_the_kinetic(at_the_source),
        ),
    )
    produced = contribution_of("horndeski_g3", "G3_of_phi_and_X")
    assert agree(produced, scaled(TO_THE_DERIVED_SIDE, right_hand_side)), SOURCE


@pytest.mark.parametrize(
    "edit",
    [
        # The sign on the piece carrying the box of the field.
        "box",
        # The factor of two in front of the mixed gradient pair, which is the
        # structure only this term produces.
        "mixed",
        # The trace piece losing the contraction of the two gradients.
        "trace",
    ],
)
def test_a_wrong_character_in_the_published_cubic_form_is_caught(edit: str) -> None:
    """The comparison above bites, which is what stops it being a tautology.

    Each of the three is a single character somebody writing that equation out
    would get wrong, and each has to fail the comparison the leg above passes.
    """
    carried = sp.Function("G3_of_phi_and_X")(PHI, KINETIC)
    at_the_source = -carried
    contraction = metric.GRADIENT_PRODUCT(KINETIC, PHI)
    box = by_the_kinetic(at_the_source) * metric.BOX(PHI)
    mixed = 2 * by_the_kinetic(at_the_source)
    trace = by_the_kinetic(at_the_source) * contraction
    if edit == "box":
        box = -box
    elif edit == "mixed":
        mixed = mixed / 2
    else:
        trace = trace * 0
    near_miss = equation(
        (
            metric.Structure(metric.METRIC),
            2 * KINETIC * by_the_field(at_the_source) - trace,
        ),
        (
            metric.Structure(metric.GRADIENT_PAIR),
            2 * by_the_field(at_the_source) + box,
        ),
        (metric.Structure(metric.MIXED_GRADIENT_PAIR, KINETIC), mixed),
    )
    produced = contribution_of("horndeski_g3", "G3_of_phi_and_X")
    assert not agree(produced, scaled(TO_THE_DERIVED_SIDE, near_miss)), edit


def degeneration(carries: str) -> tuple[metric.FieldEquation, metric.FieldEquation]:
    """The cubic term read as linear in the field, and the quadratic route to it.

    With `G3` a constant multiple of the field, `-G3 box phi` integrates by parts
    into `-2 c X`, which the `horndeski_g2` rule already varies by a route that
    shares nothing with the cubic one.
    """
    coupling = sp.Symbol(carries)
    of_phi, of_kinetic = sp.symbols("of_phi of_kinetic")
    cubic = metric.field_equation(
        one_term_action("horndeski_g3", "G3_of_phi_and_X", carries=carries)
    )
    quadratic = metric.field_equation(
        one_term_action("horndeski_g2", "G2_of_phi_and_X", carries=carries)
    )
    assert isinstance(cubic, metric.FieldEquation)
    assert isinstance(quadratic, metric.FieldEquation)
    return (
        metric.substituting(
            cubic,
            (
                {
                    sp.Function("G3_of_phi_and_X"): sp.Lambda(
                        (of_phi, of_kinetic), coupling * of_phi
                    )
                },
            ),
        ),
        metric.substituting(
            quadratic,
            (
                {
                    sp.Function("G2_of_phi_and_X"): sp.Lambda(
                        (of_phi, of_kinetic), -2 * coupling * of_kinetic
                    )
                },
            ),
        ),
    )


def test_a_cubic_term_linear_in_the_field_agrees_with_the_quadratic_route() -> None:
    """The check the published form does not give, from the other direction.

    This is evidence a comparison against a published expression cannot give,
    because it does not depend on that expression having been transcribed
    correctly. It is also the case where the mixed gradient pair leaves: the
    coefficient does not vary with the kinetic scalar, so the structure only the
    cubic term produces goes to zero, and what is left is a term the tree could
    already reach.
    """
    degenerated, already_reachable = degeneration("c")
    assert agree(degenerated, already_reachable)
    assert degenerated.terms != ()
    kinds = {shape.kind for shape, _ in degenerated.terms}
    assert metric.MIXED_GRADIENT_PAIR not in kinds


def test_the_degeneration_is_not_two_empty_equations_agreeing() -> None:
    """The near miss under the leg above, and the one it needed.

    Two equations that both came out empty agree, and a rule returning nothing
    at all for the cubic term would pass that leg. So the same comparison is made
    once more against the quadratic route read at a coefficient the degeneration
    does not produce, and it has to fail.
    """
    degenerated, _ = degeneration("c")
    coupling = sp.Symbol("c")
    of_phi, of_kinetic = sp.symbols("of_phi of_kinetic")
    quadratic = metric.field_equation(
        one_term_action("horndeski_g2", "G2_of_phi_and_X", carries="c")
    )
    assert isinstance(quadratic, metric.FieldEquation)
    wrong_sign = metric.substituting(
        quadratic,
        (
            {
                sp.Function("G2_of_phi_and_X"): sp.Lambda(
                    (of_phi, of_kinetic), 2 * coupling * of_kinetic
                )
            },
        ),
    )
    assert not agree(degenerated, wrong_sign)


def test_linearity_reaches_the_mixed_gradient_pair_too() -> None:
    """The structure only the cubic term produces obeys the rule the rest obey.

    A reading that divides by a constant puts that constant inside the gradient,
    and every published form writes it outside, so without this the comparison
    against one would be a comparison of spellings. It is asserted through
    `substituting` rather than on the helper underneath it, because that is the
    route a comparison actually takes, and it is the route that decides whether
    this structure is one the reading reaches at all.
    """
    constant = sp.Symbol("c")
    held = metric._assemble(
        [
            (
                metric.Structure(metric.MIXED_GRADIENT_PAIR, KINETIC / constant),
                sp.Integer(1),
            )
        ],
        frozenset({constant}),
    )
    rebuilt = metric.substituting(held, ())
    assert rebuilt.terms == (
        (metric.Structure(metric.MIXED_GRADIENT_PAIR, KINETIC), 1 / constant),
    )
