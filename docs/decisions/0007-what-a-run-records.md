# 0007. What a run records so a result can be reproduced

Ordered by issue #7.

## Question

What does a run of this pipeline have to write down before the number it printed
is worth anything to somebody who was not the one who ran it?

## Answer

Two halves, and both are required.

A run records the hash of the input document, the version of the pipeline, the
versions of the libraries that did the algebra, which canonicalisation
implementation was behind the seam, and the command that was run. Those five are
the smallest set from which somebody else can put the same run back together.

A second run of the same input, at the same versions, with the same
implementation behind the seam, produces byte identical output. That rules out
dictionary and set ordering reaching a result, the wall clock reaching a result,
and any unseeded randomness reaching a result. Where a field genuinely cannot be
identical between two runs, it is named as such in the output rather than
excluded quietly from the comparison.

The check that enforces the second half cites this record rather than restating
the requirement in a workflow file, so there is one place where the requirement
can be argued and one place where it changes.

## Reasons

A number out of this pipeline can end up in a paper, and a number in a paper
that nobody can reproduce is an assertion with a decimal point on it. The five
recorded facts are the ones that change the answer. Anything else about the
machine is noise, and recording noise makes the provenance block long enough
that nobody reads the part that matters.

Byte identity rather than a tolerance, because this stage is exact symbolic
work. A tolerance here would be hiding the very thing the check exists to find:
an ordering that happens to come out the same on the machine it was written on.

The requirement lives in this record rather than in the job that enforces it
because a requirement written inside a workflow file is edited by whoever is
editing the workflow, for reasons that have nothing to do with reproducibility.

## Ruled out

A result that depends on the iteration order of an unordered collection. A
timestamp, a hostname, a path or a process id reaching anything a comparison
reads. Unseeded randomness anywhere above the output. A provenance block that
names the pipeline version but not the algebra libraries, since those are where
a canonical form quietly changes. Comparing two runs with a tolerance.

## Reopened when

A stage arrives whose output genuinely cannot be made deterministic, in which
case the argument is about whether that stage belongs in this pipeline rather
than about relaxing this record.
