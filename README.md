# rechenstrasse

Testing general relativity means distinguishing metric theories, and the post-Newtonian approximation is what separates them experimentally. The route from a proposed action to field equations, PPN parameters, cosmological perturbation equations and finally numbers is walked by hand in every modified-gravity paper, usually in a private Mathematica notebook that is never published, which with the flood of f(R), scalar-tensor, Horndeski and teleparallel variants is enormous duplication that nobody can check. This pipeline takes a Lagrangian density and automates that chain. Pure symbolics, validatable against the published PPN values of known theories. It is the payoff of the indexwerk board and the reason that core is worth building.

Planning happens on the issue tracker first. Every decision that shapes
the architecture is written down there with its reasons before the code
that depends on it exists.

See [NOTICE.md](NOTICE.md) for the intended-use notice.

## Setting up a clone

The pipeline is Python with SymPy, argued in
[0002](docs/decisions/0002-the-means-for-the-pipeline.md). The interpreter build
and the whole dependency graph are fixed in the tree, in `.python-version` and
`uv.lock`, and [uv](https://docs.astral.sh/uv/getting-started/installation/) is
the tool that reads them. Install that first; everything after it is one
command.

```
uv sync --locked
```

That reads the interpreter build named in `.python-version`, fetches it if this
machine does not already have it, creates `.venv` beside the project, and
installs the packages recorded in `uv.lock` at the hashes recorded there.

`--locked` is the part that matters and it is not decoration. Without it a
restore quietly re-resolves whatever the index offers today, which is how two
clones end up with different graphs and the same green result. With it the
restore refuses in every case where the tree and the lock disagree: no lock
file, a lock that does not match `pyproject.toml`, or a recorded hash that is
not the hash the index serves. Change a dependency on purpose by running
`uv lock`, reading the diff, and committing it.

To check the environment came out right:

```
uv run python -m rechenstrasse --version
```

which prints the version in `pyproject.toml`, read back through the installed
metadata so the two cannot drift apart. The subcommands an operator will
actually run are issue #59 and do not exist yet, so a bare
`python -m rechenstrasse` prints its usage and exits non-zero instead of
looking like a run that did something.

The layout under `src/rechenstrasse/` keeps one package per pipeline stage from
the start, so a later stage that reaches into an earlier one has to write the
import and a reader can see it. The stage packages carry a docstring naming the
record or the issue that fills them in, and no code yet.

One package is not a stage. `rechenstrasse.conventions` holds the sign, index
and unit conventions of
[0008](docs/decisions/0008-sign-index-and-unit-conventions.md) as named
constants and documented functions, so that a stage reads the metric signature
instead of assuming one, and calls `riemann` in place of writing the sign out
again. Every stage below it depends on those choices and none of them may make
its own.

## Running the suite

One command, and it is the whole fast suite:

```
uv run pytest -q
```

It runs offline. That is a property of the harness and not of the machine:
`tests/conftest.py` refuses a socket, the convenience constructor that opens one
and the two name lookups that reach a resolver, for the length of the session,
and a test that reaches for any of them fails. The refusal has its own exception
type so that it can be told apart from the `OSError` a genuinely disconnected
machine gives, which is the difference between a guard that bit and a machine
that had no route. `tests/test_network_guard.py` is the proof, written as a test
that opens a socket and is expected to fail, so a guard that stopped working
reddens the suite instead of passing quietly.

The guard is a floor and not a guarantee. A test that starts a subprocess is
outside it, because the child is a fresh interpreter the harness never patched,
and so is an extension module that opens a descriptor without going through the
`socket` module.

Tests are laid out under `tests/` mirroring `src/rechenstrasse/`. Anything that
starts a second process or walks the whole tree carries the `slow` marker and is
left out of the default run:

```
uv run pytest -q -m slow
uv run pytest -q -m ""
```

The first runs only the slower half, the second runs both halves. One test
carries the marker today.

A run says what it did not run. The slow half is not the only suite the default
run leaves alone, and the others are printed by name at the end of a run with the
command that would run each:

```
uv run python tools/suites.py
uv run python tools/test_suites.py
```

The list is data in `tools/suites.py` and not a paragraph here or a line in a
workflow, because it has to fail closed in both directions and neither direction
can be tested in prose. An entry naming a file that has left the tree is refused,
so the disclosure cannot describe a suite that moved. A suite in the tree that no
entry names is refused too, which is a test file outside the directory the
default run reads, or one inside it carrying the marker that deselects it. The
second command is the proof of both, and it reads paths and the marker rather
than asking pytest's collector, so a test left out of the default run for any
other reason is outside what it can see.

Work a plain runner cannot do is not in that suite at all. Record
[0009](docs/decisions/0009-headless-tests-and-the-second-harness.md) puts it in a
second harness called `native-or-long`, with its own command and its own check:

```
uv run pytest -rs native_or_long
```

Two kinds of work belong there, anything that needs a canonicalisation core
compiled for the machine it runs on and anything long enough that nobody would
sit through it on every change, and the name says which instead of calling itself
the extended or the full suite. `-rs` is part of the command: a case in the
harness that cannot run on the machine it was started on is skipped with its
reason printed, never passed, and without that flag the reason is swallowed and
the skip is counted like a pass.

On every machine today the native case is skipped, because nothing in this tree
implements the canonicalisation seam yet and there is no compiled core to find.
What decides that is `native_or_long/seam.py`, which reads what the seam exposes
and not a name written into a test, and its own legs run everywhere, so the
harness is worth starting on a machine that can run none of its native work. The
long kind is empty for now. Neither absence is hidden behind a passing test.

Nothing in the default suite imports from the harness, and
`tests/test_harness_boundary.py` refuses it, because a module the default run
reads that reaches into the harness hands the default run the harness's
requirements.

The suite is measured, and the number does not gate:

```
uv run coverage run -m pytest
uv run coverage report
```

What is measured is the package under `src/rechenstrasse/`, configured in
`pyproject.toml` so that the number here and the number on a pull request come
from the same settings. It reads the package and not the whole tree: the rules
under `tools/` are covered by proofs that run in their own checks, and counting
them here would report covered work as uncovered.

That number gates nothing. What gates is a bar pinned on the surface that decides
an answer, which is a shorter list and is named with a reason per entry in
`tools/coverage_bar.py`:

```
uv run coverage json -o .coverage.json -q
uv run python tools/coverage_bar.py --report .coverage.json
uv run python tools/test_coverage_bar.py
```

A number over everything says very little, because a tree can carry a high one
while the code deciding whether an operator gets an answer is the part nobody
exercised. The bar fails below its number, on a report it cannot read, on a
report that matched no line on the surface, and on a surface entry the report
holds no file for. The last three matter as much as the first: an empty
measurement passing quietly is how a bar becomes decoration.

The whole-tree number is printed into the run summary of the `tests` check and
gates nothing.

## Checks you can run

Three named checks read this tree, and each one is a command you can run in a
clone. They are configured in `pyproject.toml` and not in a workflow file,
so the verdict here and the verdict on a pull request come from the same
settings.

```
uv run ruff check
uv run ruff format --check
uv run mypy
```

The first also carries the decision record rule, which the workflow runs beside
it:

```
uv run python tools/decision_records.py docs/decisions
uv run python tools/test_decision_records.py
```

A fourth check reads the invariants a single file decides on its own, under the
name `Enforce greppable invariants`. What the rules are and what each one
prevents is in `tools/invariants.py` and not in a document, because a rule
restated in prose drifts against the code that decides it:

```
uv run python tools/invariants.py
uv run python tools/test_invariants.py
```

What these do not cover. The formatter reads the Python and nothing else, so the
markdown documents and the workflow files in this tree are laid out by hand, and
nothing here refuses one for how it is laid out. That is settled and not
left open, in
[0077](docs/decisions/0077-the-documents-and-the-workflow-files-are-laid-out-by-hand.md):
a formatter over the documents would reach `docs/decisions/`, where a landed
record is not rewritten, and a tool for the workflow files has to be shown not to
move or reflow a comment first, because those comments are where the reasoning
behind each hardened setting lives. What it costs is that layout drift between
two documents is caught by a reader or not at all.

The three commands also skip `.github/pr-hygiene/`, which is a standard-library
module with a suite of its own that runs separately. That gap is recorded in
issue #17 and not only here.

`fixtures/` holds files that exist to be refused, one per check, each carrying
exactly one defect. The workflow runs every check against every fixture and
requires each fixture to be refused by its own check and accepted by the rest,
which is how a check is shown to be doing its own job instead of passing along
somebody else's red. The suite has one there too, a test whose assertion fails,
because a job that reports green whatever the suite said is the same defect one
step further out.

## What stays on the host

A theory document is often unpublished work, and it may carry a name, an
institution or an address alongside the physics.

The pipeline runs offline. It makes no network request while it computes, it
checks for no updates, it reports no crashes and it collects no usage data.
Input documents, intermediate expressions, results and run records stay on the
host. Personal data in a document stays with the document.

If a later version can send anything anywhere, it does so only because the
operator asked for that, per run, and the documentation says what would be sent
before it is sent.

Installing the pipeline is a different thing and this promise does not cover it.
The dependencies come from wherever the operator configures their package tooling
to fetch them, and the interpreter build named in `.python-version` is fetched
the same way. Both are the operator's own network activity and not the
pipeline's, and a promise that reached over them would be a promise about a
machine this project does not run.

[docs/privacy.md](docs/privacy.md) carries the same statement together with what
stands behind it, which is two guards and the gap between them and the promise.

## License

Copyright (C) 2026 Nils Lehnen. Two sets of terms, because the tree holds two
kinds of thing, and issue #12 is where that was answered.

The code is under AGPL-3.0, the GNU Affero General Public License version 3, and
[LICENSE](LICENSE) carries its full text.

The theory documents in `theories/`, the reference values, and the prose in
`docs/` and in the documents at the root are under CC BY 4.0, the Creative
Commons Attribution 4.0 International license. [LICENSE-CONTENT](LICENSE-CONTENT)
carries its full text, fetched from the source that publishes it:

```
curl -L https://creativecommons.org/licenses/by/4.0/legalcode.txt
git show HEAD:LICENSE-CONTENT | sha256sum
9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411
```

The digest is of the blob and not of a checkout, and the difference is not
pedantry. A clone with `core.autocrlf` on hands you the same bytes with a
carriage return on every line, which digests differently and is the checkout
speaking and not the tree.

The reason for the split is what a citing paper needs. A value with a citation is
content, and attribution in terms a bibliography understands is what CC BY states
and what a code license does not.

### What this tree installs from somewhere else

[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) lists every distribution in
`uv.lock` with the terms it declares about itself, and it says which of them
travel with an installed copy and which are only here to work on the tree. It is
generated, not written:

```
uv run --frozen python tools/third_party_notices.py > THIRD-PARTY-NOTICES.md
```

The same command in its refusing form is what the `lint` check runs, beside the
proof that it bites, so the file cannot drift from the lock without going red:

```
uv run --frozen python tools/third_party_notices.py --check THIRD-PARTY-NOTICES.md
uv run --frozen python tools/test_third_party_notices.py
```

Writing the notice needs an environment holding every distribution in the lock,
and it refuses by name where one is missing, because a lock carries entries that
install on one operating system and not another. Checking it verifies the terms
column only where the distribution is installed, and prints what it could not
verify instead of passing over it.

## Citing this work

[CITATION.cff](CITATION.cff) is the machine readable form, in Citation File
Format 1.2.0, and it is what the tools that build a bibliography look for.

**Cite the version you ran, not the project.** A number out of this pipeline is
a number some version of it produced, and a citation naming the project in
general tells a reader nothing about which. That is the same property record
[0007](docs/decisions/0007-what-a-run-records.md) fixes from the other side:
what a run records is the version, among four other things, precisely so that
somebody else can produce the same number.

No release carries an identifier of its own yet, so until one does, cite the
commit. It is exact, it is resolvable, and it says which bytes ran:

```
git rev-parse HEAD
```

The provenance the pipeline writes beside a result is the better source for that
number, because it is the commit that produced the result and not the one
checked out when the paper was written.

What changes when a release is cut, so that a reader coming back later is not
comparing two shapes of citation: the release carries an identifier minted for
it, [CITATION.cff](CITATION.cff) grows the version, the release date and that
identifier, and the identifier is what a bibliography entry resolves. Issue #99
is where that happens, and it also holds what is still missing, an archive
account and an identifier for the author. The citation file names neither today
instead of naming an empty one, because a key a bibliography tool resolves to
nothing is worse than a key that is absent.

The author name in the citation file is held against the copyright line above by
a case in the suite, so the two cannot come to disagree quietly.
