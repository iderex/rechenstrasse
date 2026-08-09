"""The second harness of record 0009, called `native-or-long`.

Issue #65. Everything in the default suite runs on a plain runner with no
display, no elevation and no network, and record 0009 makes those three the
definition of that run rather than a target it is held to. Work that genuinely
needs more than that lives here, and it is never folded into the default suite by
relaxing one of the three.

Two kinds of work belong here. Anything that needs a canonicalisation core
compiled for the machine it runs on, and anything long enough that nobody would
sit through it on every change. The name says what the work needs, because a
suite called extended or full turns the default one into a partial that nobody
names.

The directory is this name in the spelling Python allows for a package. The
harness, its command and its check are `native-or-long`, which is the name record
0009 gives it.

    uv run pytest -rs native_or_long

`-rs` is part of the command and not a convenience. A case here that cannot run
on the machine it was started on is skipped with its reason printed, and without
that flag the reason is swallowed and a skip reads as a pass in the count.

What is in it today. The native kind has one case, the property record 0005 puts
on the canonicalisation seam, and on every machine in existence today it skips:
nothing in this tree implements the seam yet, which is issue #33. The long kind
is empty, because no stage that produces a long derivation exists yet, and #30,
#31 and #34 are where the first one arrives. Neither absence is hidden behind a
passing test.

Nothing in the default suite may import from here, and `tests/test_harness_boundary.py`
is what refuses it. The dependency is allowed to run the other way, because the
harness exercises the same package the default suite does.
"""
