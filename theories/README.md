# The theory documents

Issue #29. Four theories from the covered class of
[0003](../docs/decisions/0003-covered-theories-and-refused-families.md), written
as documents against the schema in `rechenstrasse.document.schema`, so that every
later milestone has something real to run against and the schema is exercised by
more than one shape of input.

The four are the four entries of
[0011](../docs/decisions/0011-the-validation-corpus.md): general relativity with a
cosmological constant, Brans-Dicke, metric f(R) in the scalar-tensor form the
pipeline can take, and one case inside the covered Horndeski sector. The file name
of each is its `metadata.identifier`, so a document cannot be renamed without the
identifier a result cites moving with it, and
`tests/rechenstrasse/test_theory_documents.py` refuses the two coming apart.

## What a document here is

An input. Each one carries the reference the theory came from, in
`metadata.citation`, and the convention it is written in, in
`manifold.signature`, which is the signature record
[0008](../docs/decisions/0008-sign-index-and-unit-conventions.md) fixes and the
only one the admissibility gate accepts.

## What a document here is not

It carries no expected value, and there is nowhere in the schema to put one. The
values this pipeline is compared against live with the parity check of #42, and
the separation is the point: a change to a value cannot be hidden inside an input
file, and a number this pipeline produced cannot be promoted to an expected one by
being written here.

The convention a source used is not here either, and that is record 0008's
direction of travel rather than an omission. A published value, the convention its
source used and the translated value sit next to each other in the fixture that
holds the value, because a translation kept anywhere else drifts away from the
value it applies to.

## What schema version 1 cannot say about these theories

A term carries a head and the symbol standing in front of it, and there is no key
for what a coefficient function is. So `G4_of_phi` in `brans-dicke.json` says that
the theory carries `G4(phi) R` and which symbol stands there, and it does not say
that the function is the field itself. The four documents therefore fix the term
content of each theory and not its coefficient functions. Expressing a function is
what the reader of #25 needs and it arrives by the route record
[0004](../docs/decisions/0004-an-action-is-a-document.md) fixes, with the refusal
surface moving in the same change.

For the same reason `metric-f-of-r-as-a-scalar-tensor-theory.json` and
`covered-horndeski-sector.json` declare no parameters. What is free in them is a
function rather than a constant, and an empty list is the true statement here
while a symbol invented to fill it would not be.
