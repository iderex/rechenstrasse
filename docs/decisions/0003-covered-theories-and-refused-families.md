# 0003. Which theories the first version covers

Ordered by issue #3.

## Question

Which Lagrangians does the first version of this pipeline accept, which does it
refuse, and what happens to one it can place in neither set?

## Answer

Covered: four dimensional metric theories on a pseudo-Riemannian manifold with
the Levi-Civita connection, built from the metric, its curvature, and at most
one additional scalar field. That class contains general relativity with a
cosmological constant, scalar-tensor theories with an arbitrary coupling
function and an arbitrary potential, metric f(R) through its scalar-tensor
equivalent, and the Horndeski sector with G2 and G3 free, G4 a function of the
field alone, and G5 absent.

Refused by name, each for one reason:

G4 with kinetic dependence, and any G5, because the derivative couplings put the
theory in a regime where a plain post-Newtonian reading is not what an
experiment measures.

Teleparallel and f(T), because the geometry is torsional and every variational
step in this pipeline assumes Levi-Civita.

Vector-tensor and aether theories, because a preferred frame brings in
parameters this version does not solve for.

Bimetric and massive gravity, because a second metric is not in the internal
representation.

Quadratic curvature theories, because the extra propagating modes make the
standard metric ansatz the wrong shape of solution.

A scalar whose mass puts the range of the extra force inside the regime the
operator is asking about. This one is a property of the input rather than of a
family, so it is decided per run and not per theory.

An input the gate can place in neither set is refused as well. Silence is never
a pass, and a refusal names the family or the property it fired on rather than
only saying no.

## Reasons

A pipeline that accepts any Lagrangian and quietly produces wrong intermediate
steps for the ones outside its assumptions is worse than one that refuses them,
because the wrong intermediate steps look exactly like the right ones and end up
in a paper. Drawing the boundary before the machinery exists is what stops the
machinery from blurring it.

The covered class is not the largest one that could be made to run. It is the
one where the variational steps, the post-Newtonian expansion and the published
comparison values all hold without a case split, so agreement with the corpus
means something.

Each refusal is a different kind of boundary, which is why they are listed
separately rather than as one clause. Three of them are about the geometry or
the field content being outside the representation. Two are about the
post-Newtonian reading being the wrong description of what an experiment
measures even where the algebra would run. The last is about the input rather
than the theory.

Refusing an unplaceable input rather than passing it is the same argument in its
weakest case. A gate that passes what it did not recognise is a gate whose green
result carries no information.

## Ruled out

Accepting an input because nothing in the gate objected to it. Widening the
covered class by adding a special case to a variational step. A refusal message
that does not say which family or which property fired. Extending coverage to a
refused family without a decision record superseding this one.

## Reopened when

A refused family gets a post-Newtonian treatment in the literature that this
pipeline could reproduce, or the covered class is found to contain a theory
whose derivation needs a case split, which would mean the boundary was drawn in
the wrong place.
