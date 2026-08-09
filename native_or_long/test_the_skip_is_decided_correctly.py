"""Proof that the skip decides on what the machine has, and never on nothing.

Issue #65. The case beside this one is skipped on every machine today, so the only
thing standing between a printed skip and a silent pass is the function that
decides it. These legs run everywhere, need no core and no long derivation, and
they are why this harness is worth starting on a machine that can run none of its
native work.

Each leg hands the decision a stand-in module rather than the real seam, so all
three states are reachable here: a seam with nothing behind it, a seam holding one
operation written in Python, and a seam holding one operation that came out of a
compiled module. The last is built by pointing the stand-in at an extension
module this interpreter already carries, so the suffix being read is a real one
and not a string this file made up.
"""

import importlib
import importlib.machinery
import types
from collections.abc import Callable

import pytest

from native_or_long import seam

# Modules the standard library usually ships as extensions. Which of them is one
# is a property of the interpreter build, so the leg below reads the file rather
# than trusting this list, and skips with a reason where none of them is.
LIKELY_EXTENSIONS = ("_json", "zlib", "_struct", "select", "unicodedata")


def stand_in(**members: object) -> types.ModuleType:
    """A module object carrying the members given and nothing else public."""
    module = types.ModuleType("stand_in_for_the_seam")
    for name, value in members.items():
        setattr(module, name, value)
    return module


def a_python_operation(expression: object) -> object:
    return expression


def a_compiled_operation() -> Callable[..., object] | None:
    """One callable defined in a module this interpreter loaded from a suffix."""
    suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
    for name in LIKELY_EXTENSIONS:
        module = importlib.import_module(name)
        filename: str | None = getattr(module, "__file__", None)
        if filename is None or not filename.endswith(suffixes):
            continue
        for member, value in sorted(vars(module).items()):
            if member.startswith("_") or not callable(value):
                continue
            if getattr(value, "__module__", None) == module.__name__:
                found: Callable[..., object] = value
                return found
    return None


def test_an_empty_seam_is_a_reason_naming_the_record_and_the_issue() -> None:
    reason = seam.why_no_compiled_core(stand_in())
    assert reason is not None
    assert "0005" in reason
    assert "#33" in reason


def test_a_python_implementation_is_a_reason_of_its_own() -> None:
    reason = seam.why_no_compiled_core(stand_in(canonical=a_python_operation))
    assert reason is not None
    assert "compiled" in reason
    # Not the empty-seam reason. Two states that produce one message are one
    # state as far as the reader of a log is concerned.
    assert "#33" not in reason


def test_two_operations_on_the_seam_are_not_taken_for_one() -> None:
    # Record 0005 admits exactly one operation. A second one is a change to the
    # seam, and this harness may not pick which of the two it meant.
    reason = seam.why_no_compiled_core(
        stand_in(canonical=a_python_operation, also_canonical=a_python_operation)
    )
    assert reason is not None
    assert "2 operation(s)" in reason


def test_a_compiled_implementation_is_no_reason_to_skip() -> None:
    operation = a_compiled_operation()
    if operation is None:
        pytest.skip(
            "this interpreter carries none of the standard library modules this "
            "leg tries as an extension, so there is no real compiled suffix here "
            "to read. The build is linked differently and this leg decides "
            "nothing on it."
        )
    assert seam.is_compiled(operation)
    assert seam.why_no_compiled_core(stand_in(canonical=operation)) is None
