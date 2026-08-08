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
`python -m rechenstrasse` prints its usage and exits non-zero rather than
looking like a run that did something.

The layout under `src/rechenstrasse/` keeps one package per pipeline stage from
the start, so a later stage that reaches into an earlier one has to write the
import and a reader can see it. The stage packages carry a docstring naming the
record or the issue that fills them in, and no code yet.

One package is not a stage. `rechenstrasse.conventions` holds the sign, index
and unit conventions of
[0008](docs/decisions/0008-sign-index-and-unit-conventions.md) as named
constants and documented functions, so that a stage reads the metric signature
rather than assuming one and calls `riemann` rather than writing the sign out
again. Every stage below it depends on those choices and none of them may make
its own.

## Running the suite

One command, and it is the whole fast suite:

```
uv run pytest -q
```

It runs offline. That is a property of the harness rather than of the machine:
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

The list is data in `tools/suites.py` rather than a paragraph here or a line in a
workflow, because it has to fail closed in both directions and neither direction
can be tested in prose. An entry naming a file that has left the tree is refused,
so the disclosure cannot describe a suite that moved. A suite in the tree that no
entry names is refused too, which is a test file outside the directory the
default run reads, or one inside it carrying the marker that deselects it. The
second command is the proof of both, and it reads paths and the marker rather
than asking pytest's collector, so a test left out of the default run for any
other reason is outside what it can see.

The suite is measured, and the number does not gate:

```
uv run coverage run -m pytest
uv run coverage report
```

What is measured is the package under `src/rechenstrasse/`, configured in
`pyproject.toml` so that the number here and the number on a pull request come
from the same settings. It reads the package and not the whole tree: the rules
under `tools/` are covered by proofs that run in their own checks, and counting
them here would report covered work as uncovered. A bar that fails below a number
is issue #49 and does not exist yet, so today the number is printed and nothing
refuses a change that lowers it.

## Checks you can run

Three named checks read this tree, and each one is a command you can run in a
clone. They are configured in `pyproject.toml` rather than in a workflow file,
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
prevents is in `tools/invariants.py` rather than in a document, because a rule
restated in prose drifts against the code that decides it:

```
uv run python tools/invariants.py
uv run python tools/test_invariants.py
```

What these do not cover. The formatter reads the Python and nothing else, so the
workflow files and the documents in this tree are laid out by hand. The three
commands also skip `.github/pr-hygiene/`, which is a standard-library module
with a suite of its own that runs separately. Both gaps are recorded in issue
#17 rather than only here.

`fixtures/` holds files that exist to be refused, one per check, each carrying
exactly one defect. The workflow runs every check against every fixture and
requires each fixture to be refused by its own check and accepted by the rest,
which is how a check is shown to be doing its own job rather than passing along
somebody else's red. The suite has one there too, a test whose assertion fails,
because a job that reports green whatever the suite said is the same defect one
step further out.

## License

AGPL-3.0, the GNU Affero General Public License version 3. Copyright (C) 2026 Nils Lehnen.

See [LICENSE](LICENSE) for the full terms.
