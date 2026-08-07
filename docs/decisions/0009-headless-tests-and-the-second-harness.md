# 0009. Every test runs headless, and where the rest lives

Ordered by issue #9.

## Question

What may a test in this repository require of the machine it runs on, and where
does work that needs more than that live?

## Answer

Three prohibitions on the default suite. No display. No elevation. No network.
A test in the default suite runs on a machine with nothing installed beyond the
pinned toolchain, and a test that cannot is not in the default suite.

Work that genuinely needs more than that lives in a second harness called
`native-or-long`, with its own command and its own check name. Two kinds of work
go there: anything that needs a canonicalisation core compiled for the machine
it runs on, and anything long enough that nobody would sit through it on every
change. The name says what the work needs rather than calling itself the
extended or the full suite, because a suite called full turns the default one
into a partial that nobody names.

A case in `native-or-long` that cannot run on the machine it was started on is
skipped with the reason printed. It never passes.

The default run names `native-or-long` among the suites it did not run, together
with the command that would run it, so a green default result cannot be read as
covering more than it did.

A suite is never moved into the default run by relaxing one of the three
prohibitions. The prohibitions are the definition of the default run, not a
target it is held to.

## Reasons

This is a birth requirement rather than something to retrofit. A suite that
quietly needs one particular workstation stops being run by anybody else, and by
the time that is noticed the workstation is the only place the tree is known to
be green.

Elevation is on the list for a reason separate from the other two. A test that
raises a consent prompt takes over the machine of whoever ran it, which means it
gets run once and then skipped by hand forever after.

Printing what was not run is the difference between a green result and a green
result that can be read. Without it, the default suite and the whole set produce
the same output, and the reader has no way to tell which one they are looking
at.

Skipping with a printed reason rather than passing, because a case that reports
success without executing is worse than one that reports nothing: it is counted
in the total.

## Ruled out

A test in the default suite that opens a socket, needs a display, or asks for
elevation. A test that is made to pass by granting it one of those. A skip with
no printed reason. A default run whose output does not name what it left out.
Folding `native-or-long` into the default suite.

## Reopened when

A plain runner acquires one of the three capabilities by default, which would
make the prohibition describe something other than the machine it was written
for.
