# 0006. Where exact algebra ends and floating point begins

Ordered by issue #6.

## Question

Where in this pipeline may a floating point number appear, what is exact
everywhere above that point, and what does a number carry once it exists?

## Answer

There is one boundary and it has a name: evaluation. Above it, from the action
document down to the parameter expressions, everything is exact. Integers,
rationals, symbols and closed forms, and no float introduced by a conversion
nobody asked for or by a simplification that decided a decimal was more helpful.
At the boundary a parameter expression meets numeric values for the constants of
a theory. Below it, floating point is the point of the exercise, and a number
that comes out carries the precision it was computed at rather than the
precision of the widest thing that touched it.

A numeric value in an input document is exact where it is written exactly. A
coefficient of one half is one half and not 0.5, and a value quoted from a
source with an uncertainty is two exact numbers, the value and the uncertainty,
until evaluation.

The boundary is a place in the module layout and not a convention people
remember. Modules above it may not name a float literal, and the rule that
refuses one is the greppable invariants check of issue #19. Until that check
carries the rule, nothing refuses a float above the boundary, and the rule holds
on paper only. That is said here so it is not read as a guarantee that has not
yet been bought.

## Reasons

The comparison this board rests on is between a closed form this pipeline
derives and a closed form somebody published. A published expression can be
compared against an exact expression, by subtracting and asking whether the
difference is zero. It cannot be compared against a rounded one, because the
comparison then needs a tolerance, and a tolerance is a number somebody chose
after seeing how far apart the two sides were. Record 0011 holds the corpus that
comparison runs against, and the comparison is what makes the output checkable
rather than merely plausible.

A float above the boundary is not loud. It does not raise anything and it does
not usually change the first few digits. It changes whether two expressions that
are equal can be shown to be equal, which surfaces as a parity run that fails
for a reason nobody can find, or worse, as one that passes because the tolerance
that was added to make the first failure go away is now hiding the second.

The boundary is at evaluation rather than at export because the export of record
0043 is a rendering of exact expressions, and a rendering that rounds is a
rendering that cannot be read back. Record 0007 requires byte identical output
between two runs at the same versions, and floating point above the boundary is
one of the ways that requirement quietly stops holding across machines.

Carrying the precision with the number rather than assuming one is the same
argument as record 0007's provenance block. A number whose precision is not
recorded is a number whose agreement with a published value cannot be judged,
because the reader cannot tell a match from a rounding.

## Ruled out

A float literal in any module above the evaluation boundary. A simplification,
an evaluation shortcut or a numeric helper called above the boundary because it
was faster. Converting an exact coefficient to a decimal to make an expression
print nicely. A tolerance anywhere in the comparison between a derived
expression and a published one, which is a different thing from the tolerance
that belongs to comparing two numbers below the boundary. Reporting a number
without the precision it was computed at. Moving the boundary upward for one
stage without a record superseding this one.

## Reopened when

A theory inside the covered class of record 0003 needs a constant above the
boundary that has no exact representation, which would make the argument about
where the boundary sits rather than about whether it exists.
