# 0011. The validation corpus and where its values come from

Ordered by issue #11.

## Question

The claim that makes this board checkable is that its output agrees with values
somebody already published. Which values are those, where do they come from, and
what does agreement with them entitle anybody to say?

## Answer

The first corpus holds four entries:

General relativity, where every post-Newtonian parameter is known and most of
them vanish. It is the entry that catches a pipeline that is wrong everywhere
rather than wrong at the edges.

Brans-Dicke, where the closed form for gamma in terms of the coupling is
standard textbook material, so the comparison is against an expression rather
than against a single number.

Metric f(R) in the limit where the extra scalar is light, which is the case the
literature states a value for and the one a reader will check first.

One case inside the covered Horndeski sector for which a result has been
published, chosen so that the corpus exercises the part of the covered class
that the other three do not reach.

Every entry carries its source and the convention that source used. Not the
source alone: a value is only comparable once the conventions it was written in
are written down beside it, and the translation into this pipeline's own
conventions is recorded next to the value rather than performed in somebody's
head.

A value nobody published is not in the corpus. A number this pipeline produced,
checked by eye and then written into the expected column, is not evidence about
the pipeline. It is the pipeline's own output wearing a different hat.

Agreement with the corpus is evidence about the covered class and says nothing
whatever about the families the gate refuses. It is also evidence about the four
entries rather than about the covered class in general, and the documentation
says so in those words.

Whether a source's own table may be reproduced in the tree, as against each
value being carried with a citation, is a question about the terms those sources
are published under. This record does not settle it and does not depend on the
answer, because the citation and the convention are required either way.

## Reasons

A collection of published values is an artefact with its own failure modes, not
a heap of numbers in a test file. The failure that matters is the expected value
that drifted towards the output, and the only defence against it is that every
entry can be traced back to somebody who published it before this pipeline
existed.

Four entries rather than as many as could be found, because each one is a
maintenance obligation for as long as it sits in the tree, and four that are
always checked is worth more than twenty that are checked once.

Saying plainly what agreement does not cover, because a corpus of four theories
passing reads, to somebody skimming, like a pipeline that has been validated.
The refused families are exactly the ones where that reading would do damage.

## Ruled out

An expected value with no citation. A citation with no convention. A value
produced by this pipeline and promoted to expected. A claim that the pipeline is
validated, rather than that it agrees with these four published results. Any
statement about a refused family drawn from a corpus result.

## Reopened when

A published result appears for a covered case the four entries do not reach, or
one of the four is superseded in the literature, which makes the entry a record
of what was believed rather than a check.
