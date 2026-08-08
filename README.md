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

What these do not cover. The formatter reads the Python and nothing else, so the
workflow files and the documents in this tree are laid out by hand. The three
commands also skip `.github/pr-hygiene/`, which is a standard-library module
with a suite of its own that runs separately. Both gaps are recorded in issue
#17 rather than only here.

`fixtures/` holds files that exist to be refused, one per check, each carrying
exactly one defect. The workflow runs every check against every fixture and
requires each fixture to be refused by its own check and accepted by the other
two, which is how a check is shown to be doing its own job rather than passing
along somebody else's red.
