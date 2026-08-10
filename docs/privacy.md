# What stays on the host

What an operator puts into this pipeline is often unpublished work, and a theory
document may carry a name, an institution or an address alongside the physics.
This page says where all of that goes, which is nowhere.

Issue #54 is where the statement below was asked for, and it is written in the
same words here and in [README.md](../README.md) so that a reader who found one
of them has the whole thing.

## The statement

The pipeline runs offline. It makes no network request while it computes, it
checks for no updates, it reports no crashes and it collects no usage data.
Input documents, intermediate expressions, results and run records stay on the
host. Personal data in a document stays with the document.

If a later version can send anything anywhere, it does so only because the
operator asked for that, per run, and the documentation says what would be sent
before it is sent.

Installing the pipeline is a different thing and this promise does not cover it.
The dependencies come from wherever the operator configures their package tooling
to fetch them, and the interpreter build named in `.python-version` is fetched
the same way. Both are the operator's own network activity rather than the
pipeline's, and a promise that reached over them would be a promise about a
machine this project does not run.

## What stands behind it, and what does not

Two guards, and neither of them is the whole statement.

`no-networking-import` refuses an import that can reach the network. It reads
the source in this tree, which is `src/`, `tools/`, `.github/pr-hygiene/` and
`native_or_long/`, and it names the modules it refuses rather than guessing at
intent.

```
uv run --frozen python tools/invariants.py
```

The suite refuses the network while it runs. `tests/conftest.py` replaces the
socket constructors and the name lookups with something that raises, and
`tests/test_network_guard.py` is the proof that it bites: it opens a socket and
is red if that succeeds.

```
uv run --frozen pytest -q tests/test_network_guard.py
```

What neither of them reads is an installed dependency at run time. The import
guard reads this tree's own files and not the packages under `.venv`, and the
socket refusal is in the test harness rather than in the pipeline, so it is not
in force when an operator runs the pipeline outside a test. A dependency that
opened a socket would pass both. What holds that gap today is that the
dependency list is short, pinned by hash in `uv.lock`, and readable in
[THIRD-PARTY-NOTICES.md](../THIRD-PARTY-NOTICES.md). Issue #55 is where a
refusal that reaches a run rather than a suite is held.

## Where the pipeline writes

Not answered here. What the pipeline writes to disk, where each of those paths
is, and the command that removes each one is issue #58, and this page will point
at that answer rather than repeat it once it exists.
