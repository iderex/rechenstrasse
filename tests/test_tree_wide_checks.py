"""The one leg that reads the whole tree, and the reason it is marked slow.

Issue #14 asks the harness to separate the fast default suite from anything
slower. This is what there is to separate today: every other test in the tree
runs inside this interpreter and finishes in milliseconds, and this one starts a
second interpreter and walks every file the invariants rules read. It is the
only test carrying the marker, which is a fact about the tree today rather than
a policy, and a later test that shells out or solves something belongs here too.

`pytest -q` does not run it. `pytest -m slow` runs it and nothing else.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.slow
def test_the_tree_passes_every_greppable_invariant() -> None:
    """The invariants command accepts this tree.

    The gate runs the same command, so this is a second route to the same
    verdict rather than the only one. What it adds is that a contributor who
    runs the suite before pushing finds a refused file here instead of on the
    pull request.
    """
    finished = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "invariants.py"), str(ROOT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert finished.returncode == 0, finished.stdout + finished.stderr
