# Quality parity against the reference gate

Ordered by issue #48.

The target for the gate on this board is the gate on the jellyfin-plugin-sso
board, taken leg by leg. This document exists so that a leg this board does not
have is a stated deviation with a reason rather than an absence nobody noticed.

The target's legs were read from that repository's mainline rather than from a
checkout, at `c1c06a395399c87facfd10825ada4c08bd506926`:

    git -C <clone> fetch origin
    git rev-parse origin/main
    git grep -n -E '^name:|^    name:' origin/main -- .github/workflows/

That is a snapshot of another repository and it moves without anything here
noticing. Re-run the commands above before trusting a row. Where a job declares
no name of its own, the check appears under the job id, and both are given below
so the string a reader looks for on a pull request is unambiguous.

## The table

Status is one of adopted, meaning the same leg in the same role; adapted,
meaning the same role with the surface or the tool changed; or absent, meaning
this board does not have it and says why.

| Leg on the target board | Check string there | Status here | Check string here | Carried by |
| --- | --- | --- | --- | --- |
| Build and test | `build` | adapted | `tests` | #15 |
| Oldest supported dependency build | `ABI floor build` | adapted | `Dependency floor` | #16 |
| Package build | `Package (JPRM)` | adapted | `Build wheel` | #52 |
| Bill of materials | `Generate SBOM` | adopted | `Generate SBOM` | #52 |
| Static analysis | `Analyze (${{ matrix.language }})` | adapted | `Analyze (python)` | #18 |
| Greppable invariants | `Enforce greppable invariants` | adopted | `Enforce greppable invariants` | #19 |
| Formatting | `prettier` | adapted | `format` and `lint` | #17 |
| Sign-off | `DCO sign-off` | adopted | `DCO sign-off` | in the tree, document owed by #22 |
| Dependency review | `dependency-review` | adopted | `dependency-review` | in the tree, #53 |
| Invisible character guard | `Reject Trojan Source Unicode` | adopted | `Reject Trojan Source Unicode` | in the tree |
| Workflow audit | `Audit workflows (zizmor)` | adopted | `Audit workflows (zizmor)` | in the tree |
| Pull request hygiene | `Deterministic PR-hygiene checks` | adopted | `Deterministic PR-hygiene checks` | in the tree, #20 |
| Supply chain self-audit | `Scorecard analysis` | adopted | `Scorecard analysis` | in the tree |
| Coverage bar | a step inside `build` | adapted | a bar on the surface that decides an answer | #49 |
| Mutation testing | `Mutation testing (${{ matrix.scope.name }})` | adopted | scheduled, reported, not gating | #50 |
| Fuzzing | `Fuzz ${{ matrix.target }}` | adapted | fuzzing narrowed to the document parser | #51 |
| End to end harness | `E2E Login Harness`, job `e2e` | absent | the parity run stands in its place | #42 |
| Distribution manifest freshness | `Assert manifest-beta lists the newest beta release per generation` | absent | none | returns with #12 |
| Wiki lint | `wiki-lint` | absent | none | covered by #17 |

Legs of this board that the target does not have:

| Leg | Check string here | Carried by |
| --- | --- | --- |
| Type checking | `typecheck` | #17 |
| Determinism replay | `Determinism replay` | #21 |
| Reference value parity | `Reference value parity` | #42 |
| A second harness for work a plain runner cannot do | its own command and check name | #65 |
| The canonicalisation benchmark | reports, never gates | #66 |
| The check names required by the ruleset | not a check | #23 |

## Deviations, one line each

Build and test is adapted rather than adopted because the target's leg builds a
compiled solution and this one runs a test suite, which is the same role in a
tree with no compiler.

The oldest supported dependency build is adapted because the target holds a
binary interface floor and this board holds a library version floor, and the
failure caught is the same one: code that works against the newest and breaks
against the oldest the project claims.

The package build is adapted because the artefact is a wheel rather than a
plugin package, and the interesting half is the same in both: installing it into
an empty environment and running it.

Static analysis is adapted only in the language it analyses.

Formatting is adapted because the target runs a formatter for a language this
tree does not have, and the role splits here into a formatter and a linter.

The coverage bar is adapted because the target pins it on the modules that
decide authentication outcomes, and this board has no such modules, so it is
pinned on the modules that decide an answer, which are the admissibility gate,
the variation stage, the expansion stage and the parity comparison.

Fuzzing is adapted by being narrowed to the document parser, since that is the
only place this pipeline reads a file somebody else wrote.

The end to end login harness is absent because nothing here logs in, and the end
to end leg of this board is the reference value parity run, which is required on
every change rather than scheduled because it is cheap enough to be.

The distribution manifest freshness check is absent while nothing is published,
and it comes back if the package is published, which is an open question in #12
and is not settled here.

The wiki lint is absent because the documentation lives in this tree and is
covered by the formatting leg rather than by a separate check against a separate
wiki.

## What this table does not say

It does not say that this board's gate is as good as the target's. Most of the
rows above name an open issue rather than a check that runs, and an issue is a
plan. What carries a pull request trigger in this repository is derived rather
than counted here:

    git grep -l '^  pull_request:' origin/main -- .github/workflows/

A row marked adopted whose "carried by" column names an open issue is a leg this
board intends to have and does not have yet. The distinction is the whole value
of the table, and collapsing it would turn this document into a claim that the
parity already exists.

This paragraph is the repair for a defect it carried on the way in. It said four
checks ran on a pull request, and cited `ls .github/workflows`, which lists a
workflow that never runs on one and does not produce the number it was quoted
for. The count was also stale before anybody read it, because a leg landed
between this document being written and being merged. A number quoted with a
command that does not produce it is worse than a number with no command at all,
since the citation invites a reader not to check. The command above produces the
answer instead of decorating one.

It also does not say anything about how well any leg here works, only that it is
present or absent. Whether the coverage bar is pinned high enough, or whether
the invariants check carries the rules that matter, is what the issue carrying
each leg is for.
