# 0010. What a version number promises about a result

Ordered by issue #10.

## Question

A number out of this pipeline can be cited. What does the version number in its
provenance block promise to somebody who reads that citation later, what does it
not promise, and how does a wrong result get corrected without stranding the
people holding it?

## Answer

The version is three parts, `MAJOR.MINOR.PATCH`, and the thing being versioned
is the algebra rather than the code that carries it.

What a version promises. A given input document, at a given version, produces
the same parameter expressions as it did the first time. Across a `PATCH` or a
`MINOR` bump, every input document produces parameter expressions mathematically
equal to the ones the previous version produced, so a result cited against an
older version is still the result the newer one derives. `MINOR` is where the
pipeline gains a covered case, a refusal, an export or a command. `PATCH` is
where something is repaired that changed no expression.

What a version does not promise. Formatting. The ordering of terms inside an
expression. The internal representation of record 0005. Which implementation
sits behind the canonicalisation seam. The wording of a refusal, though not its
exit status, which issue #28 fixes separately. The byte identity that record
0007 requires holds between two runs at one version and is not promised across
versions, so a reader comparing output from two versions compares expressions
and not files.

`MAJOR` is where a parameter expression may change. It is the only place. A
conventions change under record 0008, a widened covered class that reworks a
derivation, or a repair to a wrong result all land there, and a `MAJOR` bump
carries the list of documents whose expressions moved.

How a correction is published. A wrong result is corrected by a new version and
never by a moved tag. A released version is not deleted, rebuilt or re-tagged,
because somebody's paper cites it and the thing it cites has to keep saying what
it said. The tree carries a corrections file, appended to and not rewritten, and
each entry names the versions that produced the wrong value, the input document
it was produced from, what the value was, what it is now, and the issue that
found it. A reader holding an old number has the version from the provenance
block of record 0007 and can look it up there in one place, rather than reading
release notes in sequence to find out whether their number moved.

This record fixes the scheme and the correction route. Whether releases are
published to an index, and whether a release gets a citable identifier, are open
questions belonging to the maintainer in issue #12, and this record does not
decide either and does not depend on the answers.

## Reasons

Semantic versioning is normally a promise about an interface, and here the
interface almost nobody depends on is the Python one. The thing people depend on
is the expression that came out, so the promise is written about that. A scheme
whose rules are about function signatures would let a `MINOR` bump change a
post-Newtonian parameter as long as no argument list moved, which is exactly
backwards for this pipeline.

Mathematical equality rather than byte identity across versions, because record
0007 already requires byte identity where it is meaningful, at one version, and
requiring it across versions would forbid every improvement to how an expression
is printed or ordered. Requiring it anyway would mean the promise is broken by
work that changed nothing anybody relies on, and a promise broken routinely is
one nobody checks.

A moved tag is the failure this record exists to prevent. It is cheap, it looks
like a repair, and it leaves two different artefacts in the world under one
name, one of which is on somebody's machine and cited. Nothing downstream can
tell them apart, and the provenance block of record 0007 becomes a record of
something that no longer exists.

A corrections file in the tree rather than an announcement, because the reader
who needs it is reading a paper written years ago and is not subscribed to
anything. The file is append-only for the same reason a landed decision record
is not rewritten: the state of knowledge at the time is part of what is being
recorded.

Naming the affected documents on a `MAJOR` bump, rather than saying that
expressions may have changed, because a reader cannot act on a warning that
covers everything.

## Ruled out

Moving or replacing a released tag. Deleting a released version. Publishing a
corrected result under the number that carried the wrong one. A `MINOR` or
`PATCH` bump that changes a parameter expression for any document in the tree. A
correction that exists only in release notes or only in an issue. A version
number promising the formatting or the term ordering of an expression, which
would make record 0007's byte identity a cross-version obligation. Restating
this scheme in the release documentation rather than pointing at this record.

## Reopened when

A correction has to be published for a result that no released version can be
identified as having produced, which would mean the provenance of record 0007 is
not carrying enough to make this record usable, or the covered class of record
0003 grows to a size where naming the affected documents on a `MAJOR` bump stops
being something a reader can act on.
