"""The pipeline from an action to post-Newtonian parameters.

The stages live in the sibling packages and are filled in by the later
milestones. Nothing is re-exported here, so a stage that wants another stage has
to import it by name and the reach shows up in the import line.
"""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]


def _installed_version() -> str:
    """Return the version this distribution was built with.

    The number lives in pyproject.toml and nowhere else. Reading it back through
    the installed metadata rather than restating it here means the two cannot
    disagree, which is the failure this indirection exists to prevent.
    """
    try:
        return version("rechenstrasse")
    except PackageNotFoundError as absent:  # pragma: no cover - see the message
        raise RuntimeError(
            "rechenstrasse is not installed in this environment, so its version "
            "cannot be read from the project file. Run `uv sync --locked` in a "
            "clone and use the environment that creates."
        ) from absent


__version__ = _installed_version()
