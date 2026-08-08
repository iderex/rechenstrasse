"""A module whose only defect is that it reaches past the dependency floor.

It uses one interface, `sympy.factor_system`. That name is in the algebra
library version `uv.lock` resolves to and is not in the oldest version
`pyproject.toml` allows, so this file imports on a restore from the lock and
fails to import on a restore at the floor. The `Dependency floor` check is the
only check in this tree that can tell those two runs apart, which is what makes
this a fixture for it and for nothing else.

The mistake it stands for is the ordinary one. A stage is written against
whatever the current environment happens to offer, every check on the pull
request is green because every one of them runs on that same environment, and
the operator who installed at the declared minimum meets an import error
instead of a result.

The name was not chosen by taste. It is the whole of what the two versions
differ by at the top level of the library:

    uv run --frozen python -c \
      "import sympy, json; print(json.dumps(sorted(dir(sympy))))"

run once on the lock and once on a floor restore, compared, gives
`factor_system` and `factor_cache` and nothing else.
"""

from sympy import Symbol, factor_system


def irreducible_subsystem_count() -> int:
    """Split one polynomial system and count the pieces it comes apart into."""
    x = Symbol("x")
    return len(factor_system([x**2 - 1]))


if __name__ == "__main__":
    print(irreducible_subsystem_count())
