# 0005. The internal representation, and where canonicalisation happens

Ordered by issue #5.

## Question

What do the stages of this pipeline pass to each other, and where does
canonicalisation under index symmetry sit relative to them?

## Answer

The internal representation is an expression over tensor terms with abstract
indices. An index is a named slot with a position, upper or lower, and the
symmetries belong to the tensor rather than to the term that mentions it, so
two terms naming the same tensor cannot disagree about how it behaves under an
index swap. The sign, index and unit conventions the representation is read in
are fixed separately and are not this record's to set.

Canonicalisation sits behind a seam with exactly one operation on it: take an
expression in that representation and return its canonical form. Same
expression in, same form out, for every relabelling of the dummy indices. No
other operation crosses the seam, and nothing above it may reach past it into
whatever is doing the work. A plain implementation lives in the tree from the
first day, so the pipeline is runnable before anything faster exists.

The measurement that decides whether the seam earned its cost is the benchmark
in issue #66: a fixed set of expressions from the covered theories, timed
through the seam with whichever implementation is present, with the library
versions and the machine recorded beside every number. If the time turns out to
be spent above the seam rather than inside it, the seam bought nothing and this
record is what gets argued with.

## Reasons

A seam rather than a direct dependency, because the faster core is a separate
piece of work that may land later or not at all, and this board has to be
runnable before it exists and measurably faster afterwards. If nothing here ever
reaches through the seam once a core is available, one of the two projects was
wrong about what it needed, and the seam is what makes that visible instead of
arguable.

One operation rather than a comfortable interface, because a wide one leaks the
implementation's data structures into every stage and then neither side can move
without the other. The cost of a narrow seam is that some work that could be
done cheaply on the far side gets done again on this one, and that cost is
accepted.

Symmetries on the tensor rather than on the term, because the alternative lets
one expression carry two contradictory declarations about the same object, and
that failure surfaces as a canonical form that is not canonical.

## Ruled out

A second operation on the seam without a record superseding this one. Any stage
above the seam importing from the implementation behind it. Shipping without an
in-tree implementation and treating the external core as a dependency. Deciding
the seam was worth it on the strength of anybody's expectation rather than on
the number issue #66 produces.

## Reopened when

Issue #66 reports that canonicalisation is not where the time goes, or a stage
above the seam is found to need something the single operation cannot express.
