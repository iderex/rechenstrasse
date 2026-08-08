# Contributing

This is the document a first-time contributor reads. It says what runs, what a
change has to carry, and which of the two a machine refuses.

## Before anything else, run the gate in your clone

There is no single verb here yet. The gate is a set of commands, and every one
of them is configured in `pyproject.toml` rather than in a workflow file, so the
verdict you get in a clone and the verdict on the pull request come from the same
settings and cannot disagree about a rule.

Set the clone up once, as described in the "Setting up a clone" section of
[README.md](README.md):

```
uv sync --locked
```

Then run all of it:

```
uv run --frozen pytest -q
uv run --frozen ruff check
uv run --frozen ruff format --check
uv run --frozen mypy
uv run --frozen python tools/decision_records.py docs/decisions
uv run --frozen python tools/test_decision_records.py
uv run --frozen python tools/invariants.py
uv run --frozen python tools/test_invariants.py
uv run --frozen python tools/test_suites.py
python3 .github/pr-hygiene/test_hygiene.py
```

The first line is the fast half of the suite. `pytest -q -m slow` runs the other
half and `pytest -q -m ""` runs both, and the slow half is worth running before
you push because it walks the whole tree. A run prints, at its end, the suites it
did not run and the command for each, so a green result cannot be read as
covering more than it did.

Two checks on the pull request have no useful local form and are listed here so
that the absence is visible rather than surprising. The dependency review reads
the diff against an advisory database on the server. The hygiene check reads the
pull request itself, which does not exist until you open one, and the command
above runs that check's own suite rather than the check.

## Every change starts as an issue and lands as a pull request

Direct pushes to the default branch are refused. The issue is where the argument
happens and the pull request is where the change is read, and an issue that
exists only to justify a diff already written is the wrong way round.

An issue says what is wrong, what the evidence is, and what "done" means. If the
evidence is a number, it carries the command that produced it. The done-when is
what somebody else will measure the change against, so write it as something
that can be checked rather than as an intention.

A pull request body carries the same obligation, one step sharper. Every asserted
fact in it carries the command that produced it, run at the commit being pushed
and against the reference the reader will have rather than against your working
tree. Where a claim cannot be backed by a command, write it as a claim. A number
pasted from a run of something else is the largest defect class this style exists
against.

Say what the change does not cover, in the same body, in the same voice. A
statement that a check was not run, or that a surface was not measured, survives
every edit of the body and never turns into a statement that it was.

## What is refused and what is asked for

The difference matters, because a request read as a guarantee is worse than no
request at all.

A machine refuses these. A commit without a sign-off trailer matching its author.
A pull request with an empty body, or one naming no issue. A commit message that
is a subject line and nothing else. A change to a generated file with no
`Regenerated: <path>` line in the body. A head branch that is the default branch.
An action referenced by a tag rather than by a commit. A write permission granted
at the workflow level. A checkout that persists credentials. A bidirectional or
invisible Unicode control character in tracked text. A float literal above the
evaluation boundary, an import that can reach the network, a catch-all `except`,
and a test reading an absolute path or a home directory, each within the
directories the rule names in `tools/invariants.py`. A decision record missing
one of its five sections. A test file the disclosure in `tools/suites.py` does
not name, and an entry in it naming a file that has left the tree. Everything the
linter, the formatter and the type checker decide.

Prose asks for the rest, and nothing in this tree refuses a violation of it. That
every asserted fact carries its command. That a commit message says what changed
and what failure it prevents. That one commit and one pull request carry one
topic. That a claim written in a document is true. Those are what review is for.

## No guard ships without proof that it bites

A check that cannot fail is a check nobody is running. Every check in this tree
carries, in its own job and on the same commit, a step that makes it fail on
purpose: a file in `fixtures/` whose only defect is the one that check exists to
catch, which every other check has to accept, or a copy of the tree with the
mistake planted in it. Adding a check without that step is not adding a check.

Spend the effort on the near miss. A fixture that could not have passed proves
less than one that nearly did, so pick the one-character mistake somebody will
actually make.

## Where the decisions live

`docs/decisions/`. A record carries five sections and its number is the number of
the issue that decided it, which is
[0001](docs/decisions/0001-the-shape-of-a-decision-record.md), and
`docs/decisions/0000-template.md` is the shape. A landed record is not rewritten:
a decision that changes is superseded by a new record naming the one it replaces.
Read the record before arguing with something it decided, because most
disagreements about a rule here are disagreements about a record.

## Widening what the pipeline accepts

A contribution that widens what the pipeline reads widens the refusal surface in
the same change, or says in its body why it does not.

That rule is not this document's. It is decided in
[0004](docs/decisions/0004-an-action-is-a-document.md), which fixes the route the
schema grows by, and the record rather than this paragraph is what a reader
should be sent to. What it comes down to is that a term nobody can express today
arrives with an issue naming it, a schema version carrying it, a fixture document
using it, and the matching case in the admissibility gate, so the accepted
surface and the refused surface move together. A term the schema has no head for
is refused with that head named and is never handed to something that will try
its luck.

## Signing off

Every non-merge commit carries a `Signed-off-by:` trailer whose name and address
match the commit's author. That is the assertion in [DCO](DCO), which is the
Developer Certificate of Origin 1.1, unchanged. `git commit -s` writes the
trailer for you.

```
git commit -s -m "..."
```

The certificate says you have the right to submit the contribution under the open
source license indicated in the file. No license is in this tree yet. Which one
it will be is the first question in issue #12 and it belongs to the maintainer,
so until it is answered a sign-off here asserts your right to submit rather than
the terms you are submitting under. That gap is the reason the question is at the
top of that issue.

## The checks, by the name each one carries on a pull request

The string in the first column is what appears next to a run on the pull request.
Where a check has a local form, the second column is the command that decides the
same thing in a clone.

| On the pull request | In a clone |
| --- | --- |
| `tests` | `uv run --frozen pytest -q` |
| `lint` | `uv run --frozen ruff check` |
| `format` | `uv run --frozen ruff format --check` |
| `typecheck` | `uv run --frozen mypy` |
| `Enforce greppable invariants` | `uv run --frozen python tools/invariants.py` |
| `Dependency floor` | `uv lock --resolution lowest-direct`, then `uv sync --frozen --no-group quality`, then `uv run --frozen --no-group quality pytest -q`, in a copy of the tree |
| `Locked environment restores (ubuntu-latest)` | `uv sync --locked` |
| `Locked environment restores (macos-latest)` | the same, on that platform |
| `Locked environment restores (windows-latest)` | the same, on that platform |
| `DCO sign-off` | `git log --format=%B` and read the trailers |
| `Deterministic PR-hygiene checks` | `python3 .github/pr-hygiene/test_hygiene.py`, which is the check's own suite rather than the check |
| `Reject Trojan Source Unicode` | the pattern and the `git grep` that reads it are in `.github/workflows/unicode-guard.yml` |
| `Audit workflows (zizmor)` | `uvx --no-build "zizmor@<version>" --strict-collection --min-severity=low --format=plain .`, at the version pinned in `.github/workflows/zizmor.yml` |
| `zizmor` | none, and it is not the row above. Code scanning reports it after that job uploads its results, and it says whether the change introduced a new alert |
| `dependency-review` | none, it reads the diff against an advisory database on the server |

The decision record rule runs inside `lint` rather than under a name of its own,
which is why no row above carries it. `Scorecard analysis` is not in the table
because it does not run on a pull request; it runs on the default branch and on a
schedule.

Nothing in this tree reads this table. A check renamed, added or removed leaves it
stale and every route stays green, which is exactly the drift a list written in a
document always has. Issue #86 is where the mechanism that would refuse a stale
row is owed. Until it lands, the authority for what runs is
`.github/workflows/`, and the way to get the strings without trusting this page
is to read them off an open pull request:

```
gh api repos/iderex/rechenstrasse/commits/<head sha>/check-runs \
  --jq '[.check_runs[].name] | unique | .[]'
```

## What this document does not cover

It says nothing about which of the checks are required before a merge. That is a
setting on the default branch rather than a fact of this tree, and issue #23 is
where it is decided and written down.

Milestone 2 is not finished, and issues still open in it add checks that do not
exist yet, so the table above will move before that milestone closes.
