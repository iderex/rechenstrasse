# 0001. The shape of a decision record

Ordered by issue #1.

## Question

What has to be in a file under `docs/decisions/` before it counts as a decision
record, what number does it carry, and what happens when the decision changes?

## Answer

A decision record carries five sections, with these headings and these names:
`## Question`, `## Answer`, `## Reasons`, `## Ruled out`, `## Reopened when`.
`docs/decisions/0000-template.md` is the shape they take. A file under
`docs/decisions/` missing any one of the five is not a decision record.

The number in the filename is the number of the issue that decided the thing.
Numbers therefore only ever go up, no number is ever reused, and the file points
straight at the argument that produced it.

A landed record is not rewritten. A decision that changes is superseded by a new
record carrying a sixth section, `## Supersedes`, naming the record it replaces,
and the replaced record stays in the tree unchanged.

## Reasons

The five sections are the smallest set that makes a record arguable. The
question fixes the scope, the answer is what holds now, the reasons let somebody
disagree with the argument rather than with the outcome, the exclusions say what
the answer costs, and the reopening condition is what keeps a record from
outliving the situation it was written for. Prose with none of those is a note,
and a directory of notes is a place people stop looking.

The number comes from the issue rather than from a running count because a
running count is chosen by reading the directory, and two records written
against the same directory choose the same next number. Nothing about that
collision is loud: both files add cleanly and the tree ends up with two records
numbered 0001. Deriving the number from the issue makes the collision
impossible rather than detectable, and it costs the contiguity of the sequence,
which nothing reads.

Superseding rather than editing keeps the reasoning that was live when the code
was written. The alternative, editing the record in place, leaves a tree whose
decisions all look as though they were obvious from the start.

## Ruled out

A record with no reopening condition. A record edited after it lands. Two
records carrying one number. A decision that lives only in an issue comment or
only in a commit message, because neither is where somebody reading the code
will look for it.

## Reopened when

A checker over these files needs a field the five headings cannot carry, or the
issue-derived numbering produces a directory nobody can read in order.
