# 0077. The documents and the workflow files are laid out by hand

Ordered by issue #77.

## Question

The `format` check reads the Python in this tree and nothing else. Are the
markdown documents and the workflow files brought under a formatter as well, and
if not, where does a reader meet that fact?

## Answer

They are not. No tool formats the markdown documents or the workflow files in
this tree, and nothing here refuses one for how it is laid out. Their layout is
decided by whoever writes them and, where it is wrong enough to matter, in
review.

That is a decision and not a gap left open. It is stated where a reader meets
the rule: in `README.md` beside the commands that do run, and in the header
comment of `.github/workflows/format.yml`, which is the file somebody opens to
find out what `format` covers. Both point here for the reason rather than
carrying their own version of it.

Record 0001 is untouched by this. A landed record is not rewritten, without an
exception for a formatting-only change, and nothing here reads that rule
differently.

## Reasons

A formatter over the documents would reach `docs/decisions/`, and a landed
record in that directory is not rewritten. That leaves three ways forward and
each costs something different.

Adopting a formatter over everything means treating a formatting-only change as
not a rewrite. That is a reading of record 0001, and it is the reading that makes
the rule conditional: the first exception is taken for the convenience of a tool,
and the rule is weaker afterwards for every reason somebody brings next. The
directory exists so that the reasoning live when a decision was made survives
unedited, and a tool that touches those bytes at all is arguing with that.

Adopting a formatter and holding `docs/decisions/` outside it keeps record 0001
absolute and costs the opposite thing: the one directory a reader most wants to
find consistent is the one directory the tool does not read. An exclusion also
grows. New records would have to be written in the shape the formatter would
produce, by hand, which is the state this answer is in already, with an extra
dependency paying for it.

The workflow files are a separate question and are answered the same way for a
different reason. Every workflow in this tree carries a long comment block, and
those comments are where the reasoning behind each hardened setting lives. A tool
proposed for them has to be shown not to move or reflow a comment, and that
measurement has not been made. Adopting one on the expectation that it behaves is
the shape of decision this tree does not take.

What this answer costs is real and is not hidden by stating it. Layout drift
between two documents is caught by a reader or not at all, and a formatting
argument in a review is time spent on nothing, which is the thing the `format`
check exists against for the Python. That cost is accepted here because it falls
on prose, where a wrong layout is ugly, rather than on code, where the same
argument recurs on every change.

## Ruled out

A formatter over `docs/decisions/`, in any configuration, while record 0001
stands as written. A formatting-only exception to "a landed record is not
rewritten", which would be a reading of record 0001 and would need a record
superseding it rather than a line in a workflow file. A tool over the workflow
files adopted before it is shown, on this tree, not to move or reflow a comment.
A statement that these files are laid out by hand living only in an issue, which
is where it lived until this record.

## Reopened when

A markdown formatter is shown, on this tree, to leave every file under
`docs/decisions/` byte identical, which removes the conflict with record 0001
entirely and makes the first option cost nothing. Or record 0001 is superseded on
its own argument, by a record that decides what a rewrite is, in which case this
answer rests on a rule that no longer says what it said. Or a formatting argument
in a review over one of these files costs enough time that the cost accepted
above turns out to be the larger one.
