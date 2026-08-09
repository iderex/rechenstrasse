"""The native case: the seam's property, exercised where a compiled core exists.

Issue #65. Record 0005 puts one operation on the canonicalisation seam and one
property on it: the same expression in gives the same canonical form out, for
every relabelling of its dummy indices. Exercising that against a core compiled
for the machine it runs on is work a plain runner cannot do, which is why the
case is here and not in the default suite.

On every machine today this case is skipped, and the reason is printed: nothing
in this tree implements the seam yet. The skip is decided by `seam.py`, which
reads what the seam exposes rather than a name written into this file.

What this case does not yet assert. The relabelling property needs the internal
representation of record 0005 to build two expressions out of, and that arrives
with the reader of #25. Until then it asserts what the tree admits: that the seam
carries exactly one operation and that the operation comes from a module compiled
for this machine. It is extended there rather than replaced, and the name of the
operation is deliberately not written here.

The requirement is asserted inside the case as well as in the skip above it. That
is not redundancy. A skip condition that answers wrongly would otherwise let this
case pass on a machine that does not meet what it says it needs, which is the one
outcome record 0009 rules out.
"""

import pytest

from native_or_long import seam

REASON = seam.why_no_compiled_core(seam.seam_package())


@pytest.mark.skipif(REASON is not None, reason=str(REASON))
def test_the_seam_takes_one_expression_and_returns_a_canonical_form() -> None:
    package = seam.seam_package()
    operation = seam.implementation(package)
    assert operation is not None, "the skip above should have caught this"
    assert seam.is_compiled(operation), (
        "this case runs only against a core compiled for this machine, and the "
        "skip above is what decides that"
    )
