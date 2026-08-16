# 0008. The sign, index and unit conventions

Ordered by issue #8.

## Question

Which conventions does every stage of this pipeline read and write in, so that
no stage has to assume one, and what happens to a published value that was
written in a different set?

## Answer

One set, fixed here, used everywhere. It is the set Misner, Thorne and Wheeler
use, and what this repository is held to is the formulas below, not the
citation, so a reader can check the tree against the page and not against a
book title.

The metric signature is `(-, +, +, +)`. A timelike interval is negative.

The connection is the Levi-Civita connection of that metric, which record 0003
already made a condition of the covered class:

    Gamma^r_{mn} = 1/2 g^{rs} ( d_m g_{sn} + d_n g_{sm} - d_s g_{mn} )

The Riemann tensor is

    R^r_{smn} = d_m Gamma^r_{ns} - d_n Gamma^r_{ms}
              + Gamma^r_{ml} Gamma^l_{ns} - Gamma^r_{nl} Gamma^l_{ms}

The Ricci tensor is the contraction of the first upper index against the third
lower one, `R_{mn} = R^l_{mln}`, the Ricci scalar is `R = g^{mn} R_{mn}`, and
the Einstein tensor is `G_{mn} = R_{mn} - 1/2 R g_{mn}`. With these three
choices a sphere has positive scalar curvature and de Sitter space has a
positive cosmological constant.

The field equations carry the cosmological constant on the geometry side, with
the symbol `Lambda`:

    G_{mn} + Lambda g_{mn} = 8 pi G T_{mn}

Units are geometrised in the speed of light only. `c` is 1. The gravitational
coupling stays visible as `8 pi G` and is not absorbed into the normalisation of
a field or a coupling function. A theory written with the reduced Planck mass
declares `M^2 = 1 / (8 pi G)` in its own document and the pipeline reads the
translation instead of inferring it.

Index conventions. Indices are the abstract named slots of record 0005, and the
order a tensor's indices are written in is the order they mean. Nothing
rearranges them silently. Indices are raised and lowered only with the metric
fixed above. Symmetrisation and antisymmetrisation carry the factorial weight,
so `T_{(mn)}` is `1/2 (T_{mn} + T_{nm})` and `n` indices carry `1/n!`.

The scalar sector. The kinetic scalar is

    X = -1/2 g^{mn} (grad_m phi)(grad_n phi)

so `X` is positive for a field whose gradient is timelike, which is the
homogeneous case milestone 6 works in. Inside the covered Horndeski sector of
record 0003 the terms are `G2(phi, X)`, `-G3(phi, X) box phi`, and
`G4(phi) R`, with the sign on the third term the one written here. A potential
enters through `G2`, and a theory that writes its cosmological constant as a
constant term in the potential declares that translation in its document rather
than leaving the same constant in two places.

The post-Newtonian reading. The Newtonian potential `U` is positive, defined by
`lap U = -4 pi G rho`, and the first order metric is `g_{00} = -1 + 2 U` with
`g_{ij} = (1 + 2 gamma U) delta_{ij}`. That is the reading in which general
relativity has `gamma = 1` and `beta = 1`, and it is the sign that decides
whether a parameter comes out with the sign the corpus of record 0011 expects.

A source that used a different set is not translated in somebody's head. Record
0011 requires each corpus entry to carry the convention its source used, and
this record fixes the direction of travel: the fixture holds the value as the
source published it, the convention that source used, and the translated value,
next to each other in the fixture. A translation performed in a comment, in a
commit message or during review is not a translation this repository has.

Each convention above becomes one named constant or one documented function in
the code that uses it, not an assumption repeated in several modules. No code
exists in the tree yet, so today the conventions above are written down here and
nowhere else, and nothing refuses a stage that assumes its own signature. Issue
#8 stays open for that half.

## Reasons

A sign convention is the cheapest available source of a wrong answer that looks
right. Every stage downstream inherits whatever the first one assumed, and a
flipped Riemann sign does not produce nonsense. It produces field equations that
are structurally correct and off by a minus, which survive review, survive the
identity checks of issue #34 in some cases, and surface at the parity comparison
as a disagreement nobody can localise because both sides look reasonable.

Fixing them before anything uses them, and not when the first disagreement
appears, is the point. After the fact, the convention is chosen by whichever
answer the fix makes match, which is fitting the convention to the result.

Keeping `G` visible instead of setting it to 1 is not a stylistic choice. In a
scalar-tensor theory the constant in the field equations and the constant a
Cavendish experiment measures are different numbers, and the relation between
them is part of what the post-Newtonian stage computes. Absorbing one into the
other makes the difference invisible at exactly the stage that exists to
measure it.

The cosmological constant on the geometry side, with one symbol, because the
alternative is a theory whose document carries it twice, once as `Lambda` and
once inside a potential, and a pipeline that adds both. Requiring the
declaration in the document instead of detecting it is record 0004's rule
applied here: the input says what it means and the pipeline does not guess.

The factorial weight is stated because both conventions are in use and the
difference is a factor of two in every antisymmetrised term. It is the kind of
thing everybody knows and nobody writes down, until two stages written at
different times disagree.

Putting the translation inside the fixture, next to the quoted value, is the
same argument as the one record 0011 makes about citations. A translation kept
anywhere else drifts away from the value it applies to, and the fixture then
asserts a number whose provenance says something that is no longer true of it.

## Ruled out

A stage that assumes a signature instead of reading the one named here. A
second convention held anywhere in the tree for convenience, including inside a
single fixture. A convention documented only in a comment. Translating a
published value without recording the source convention and the translation
beside it. Setting `G` to 1. Carrying the cosmological constant on both sides of
the field equations or in two places in one document. Changing any convention
above without a record superseding this one, since a change here silently
invalidates every fixture in the tree.

## Reopened when

A theory inside the covered class of record 0003 cannot be written in this set
without a case split, or the corpus of record 0011 gains an entry whose source
convention has no expressible translation into it, either of which would mean
the set was chosen for the wrong class of problem.
