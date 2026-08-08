"""What is behind the canonicalisation seam in this environment, if anything.

Issue #65. A case in this harness that needs a compiled core has to decide, on
the machine it was started on, whether that core is there. The answer decides
between running the case and skipping it with a reason, and it may never decide
between running it and passing it.

The question is asked of the seam of record 0005 rather than of a name written
here. That record puts exactly one operation on the seam, take an expression and
return its canonical form, and says nothing above the seam may reach past it, so
this module reads what the seam package exposes and does not import anything
behind it.

Two answers, and they are different states rather than degrees of the same one.

  nothing behind the seam
      The seam package exposes no operation at all. Nothing in this tree
      implements it yet and issue #33 is where the plain implementation arrives.
      Every machine is in this state today.

  an implementation that is not compiled
      Something is behind the seam and it is Python. The plain implementation is
      what record 0005 asks to exist from the first day, and a case that exists
      to measure or exercise a compiled core has nothing to run against.

A compiled implementation is one whose module file carries an extension suffix
this interpreter recognises, which is read from the interpreter rather than
written out here, because the set of suffixes is a property of the build and not
of this repository.
"""

import importlib
import importlib.machinery
from collections.abc import Callable
from types import ModuleType

# The package that holds the seam. Named as a string and imported through the
# import system, because nothing here may reach past the seam to whatever
# implements it and a direct import of the implementation would be exactly that.
SEAM = "rechenstrasse.canonical"


def seam_package() -> ModuleType:
    return importlib.import_module(SEAM)


def operations(module: ModuleType) -> list[str]:
    """The public callables the seam exposes, sorted.

    Record 0005 admits exactly one. This returns the list rather than the one,
    so a second operation appearing on the seam is visible to a reader of a run
    instead of being silently taken as the first.
    """
    return sorted(
        name
        for name, value in vars(module).items()
        if not name.startswith("_") and callable(value)
    )


def implementation(module: ModuleType) -> Callable[..., object] | None:
    """The one operation on the seam, or None where the seam is empty."""
    found = operations(module)
    if len(found) != 1:
        return None
    value = getattr(module, found[0])
    return value if callable(value) else None


def is_compiled(operation: Callable[..., object]) -> bool:
    """True where the operation comes from a module compiled for this machine.

    Read from the module the operation was defined in, and from the suffixes
    this interpreter accepts for an extension, so a core built for one platform
    is not taken for one built for another by a name comparison.
    """
    home = getattr(operation, "__module__", None)
    if home is None:
        return False
    module = importlib.import_module(home)
    filename: str | None = getattr(module, "__file__", None)
    if filename is None:
        return False
    return filename.endswith(tuple(importlib.machinery.EXTENSION_SUFFIXES))


def why_no_compiled_core(module: ModuleType) -> str | None:
    """The reason a case needing a compiled core cannot run, or None if it can.

    A string rather than a boolean, because the reason is the part that has to
    reach the log. A skip whose reason is not printed is counted in the total
    and reads as a pass.
    """
    operation = implementation(module)
    if operation is None:
        return (
            f"nothing is behind the canonicalisation seam of record 0005 in this "
            f"environment: {SEAM} exposes {len(operations(module))} operation(s) "
            "and the record admits exactly one. The plain implementation is "
            "issue #33 and there is no compiled core in this tree to detect."
        )
    if not is_compiled(operation):
        return (
            "the implementation behind the canonicalisation seam is Python and "
            "not a core compiled for this machine, so a case that exists to "
            "exercise a compiled one has nothing to run against here. Issue #66 "
            "is where the two are measured against each other."
        )
    return None
