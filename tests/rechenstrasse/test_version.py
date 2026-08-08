"""The version the package reports is the one the project file declares.

Issue #14. `rechenstrasse.__version__` is read back through the installed
metadata rather than restated in the source, and the whole value of that
indirection is that the two cannot disagree. Nothing was checking that it holds,
so an environment restored from a stale build would report the old number and
every provenance block written in that environment would carry it.
"""

import tomllib
from pathlib import Path

from rechenstrasse import __version__

# tests/rechenstrasse/test_version.py -> the clone this file is part of. A path
# relative to this file rather than to the working directory, so the assertion
# means the same thing from any directory the suite is started in.
PROJECT_FILE = Path(__file__).resolve().parents[2] / "pyproject.toml"


def test_the_reported_version_is_the_declared_one() -> None:
    declared = tomllib.loads(PROJECT_FILE.read_text(encoding="utf-8"))
    assert __version__ == declared["project"]["version"]
