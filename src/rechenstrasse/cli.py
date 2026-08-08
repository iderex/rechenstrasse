"""The entry point behind `python -m rechenstrasse`.

What an operator actually runs is issue #59 and is not decided here. This module
carries the one flag the toolchain issue owes, `--version`, so that a clone that
built correctly can be told apart from one that did not.
"""

import argparse
from collections.abc import Sequence

from rechenstrasse import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rechenstrasse",
        description=(
            "Derive field equations, post-Newtonian parameters and "
            "perturbation equations from an action."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="print the version this environment was built at, and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    # No subcommand exists yet. Printing the help and returning a non-zero
    # status keeps a bare invocation from reading as a run that did something.
    parser.print_help()
    return 2
