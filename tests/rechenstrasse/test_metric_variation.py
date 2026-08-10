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

The near misses are the last three legs. Each one is a single character somebody
would actually get wrong: the sign of the piece the connection variation leaves
behind, the factor of one half in front of the trace term, and the sign of the
kinetic contribution. Each is asserted to fail the same comparison the leg above
it passes, which is what stops those legs from being three ways of writing
`True`.
"""

import json
from pathlib import Path

import pytest
import sympy as sp

from rechenstrasse.admissibility import gate
from rechenstrasse.document import reader
from rechenstrasse.representation import Action, Lagrangian, Tensor, Term
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


def test_the_covered_heads_are_varied_or_named_as_not_derived() -> None:
    """Every head the gate covers has a rule here or is named as having none.

    This is what holds the accepted surface and the derived surface together. A
    head widened into the covered class without a variation rule would otherwise
    arrive here as a term nothing varies, and the equation for a document
    carrying it would be missing a term rather than absent.
    """
    assert set(gate.COVERED_HEADS) == set(metric.RULES) | set(metric.NOT_DERIVED)
    assert set(metric.RULES).isdisjoint(metric.NOT_DERIVED)


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


def test_every_theory_document_in_the_tree_is_varied_or_says_why_not() -> None:
    """No document reaches a half derived equation, and none is silently skipped."""
    stems = sorted(path.stem for path in THEORIES.glob("*.json"))
    assert stems, f"no theory document below {THEORIES}, which is not a pass"
    for stem in stems:
        produced = metric.field_equation(action_of(stem))
        if isinstance(produced, metric.NotDerived):
            assert produced.reasons != ()
            for reason in produced.reasons:
                assert reason.split(":")[0] in metric.NOT_DERIVED
        else:
            assert produced.terms != ()


def test_the_covered_horndeski_document_produces_no_equation_and_names_the_head() -> (
    None
):
    """The one document in the tree this stage does not reach, and what it says.

    A field equation missing one term of the action is wrong in the way that
    looks right, so the whole document produces nothing rather than three terms
    out of four. What comes back is not a refusal: no record drew a line this
    theory is outside, and the reason says which issue holds the work.
    """
    produced = metric.field_equation(action_of("covered-horndeski-sector"))
    assert isinstance(produced, metric.NotDerived)
    assert len(produced.reasons) == 1
    assert produced.reasons[0].startswith("horndeski_g3:")
    assert "#114" in produced.reasons[0]


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
