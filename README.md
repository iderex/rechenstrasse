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
