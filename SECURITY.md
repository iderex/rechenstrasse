# Security policy

## What this program is, so a report can be about it

`rechenstrasse` is a library that runs in one process on the machine an operator
started it on. It reads a theory document, which is JSON describing a
gravitational action, decides whether the theory that document describes is
inside the class this pipeline will answer for, and derives the metric field
equations symbolically with SymPy. There is no server, no account, no session,
no database and no network listener anywhere in it.

Outside the standard library, the whole of `src/rechenstrasse/` imports nothing
but SymPy. The standard-library half, counted across all 20 modules, is
`dataclasses`, `typing`, `collections.abc`, `json`, `argparse`,
`importlib.metadata`, `itertools`, `math` and `sys`. It opens no socket, reads
and writes no file, starts no subprocess and consults no environment variable.
Even the input arrives as text rather than as a path: `document.reader.read`
takes the bytes of a document, and whatever opened that file was the operator's
own code. `python -m rechenstrasse` carries one flag today, `--version`, and
otherwise prints its usage and exits non-zero, because the subcommands an
operator would actually run are issue #59 and do not exist yet.

So there is nothing here to take over, nothing to escalate to, and nothing
listening to be reached. What there is, is a parser that eats a file somebody
else wrote, symbolic algebra downstream of it, a published promise about what
stays on the host, and eighteen workflow files, most of which run against pull
requests from strangers.

## Where to report

Report privately through GitHub Security Advisories:

https://github.com/iderex/rechenstrasse/security/advisories/new

That door opens. Measured today:

```
$ gh api repos/iderex/rechenstrasse/private-vulnerability-reporting
{"enabled":true}
```

Please do not open a public issue for something you believe is exploitable
against a person running this. Everything else is better in the open, on the
issue tracker, where it gets fixed faster and where somebody else hitting the
same thing can find it.

### No response deadline

I promise no acknowledgement time and no fix time, and that is deliberate. A
deadline this project cannot hold is worse than none: a reporter told to expect
an answer within so many days and left without one cannot tell a slow maintainer
from a report that never arrived, and has to start over guessing which. There is
no number here for that reason. I read the advisory queue.

## Which version to report against

There is no release, no tag and no package on PyPI, so there is no
supported-versions table to give you. The only thing that exists to report
against is a commit on `main`, and a fix lands there. Name the commit you saw it
on:

```
git rev-parse HEAD
```

Anything before that commit is history and nothing gets backported to it.

## The surface that is real here

**The document reader, which is the one thing that eats input from elsewhere.**
`src/rechenstrasse/document/schema.py`, `reader.py` and `positions.py`. A theory
document is often somebody else's file: sent by a colleague, taken out of a
paper's supplement, or pulled from a repository. The reader's contract is that
it returns a refusal and never raises, so anything that makes it raise instead
of refusing is a defect in it, and any input that makes it exhaust the stack or
run away is worth reporting. `fuzz/crashes/` already carries two such inputs, a
document nested deeply enough to take the loader's recursion over the edge and a
mapping carrying one key twice, and `tools/fuzz.py` replays both on every run so
that neither can come back quietly. A third of that kind is welcome.

**A document read as a theory other than the one written.** This is the failure
the whole board exists against, and it is worse here than a crash. The duplicate
key above is the shape of it: the loader keeps the last of the two and says
nothing, so a document that said two things reads as one. If you have an input
that the reader accepts, that produces an action, and whose action is not what
the document says, that is the report I most want.

**Anything that turns a document string into something evaluated.** Document
strings become SymPy names in `src/rechenstrasse/variation/metric.py`, through
`sp.Symbol(term.coefficient)` and `sp.Function(term.coefficient)(scalar)`. Those
name a symbol; they do not parse an expression, and record 0004 rules out an
expression parser precisely so that a term cannot be read as something other
than what its author meant. If you find a route by which text out of a document
reaches `sympify`, `parse_expr`, `eval`, an import, or anything else that
executes, treat it as the highest-value finding in this tree and use the
advisory channel.

**Work out of proportion to the input.** The reader refuses a document nesting
past `NESTING_LIMIT`, which is 100, before the loader runs. Nothing else is
bounded: the number of terms, the length of a symbol, and what the algebra then
does with them are all open. A small document that costs a great deal of memory
or time is worth a report, especially if you can state the ratio, because
anybody who wires this behind a queue inherits it.

**The claim in `docs/privacy.md` and in the README.** It says the pipeline makes
no network request, collects nothing, and leaves the input on the host. That is
a promise and it is checkable. If a stage in this tree opens a socket, writes
outside where it was pointed, or carries a document's contents anywhere, that
contradicts something published and I want it privately first. The gap is
already written down there: the import guard reads this tree and not the
installed packages, and the socket refusal lives in the test harness rather than
in the pipeline, so a dependency that opened one would pass both.

**Continuous integration.** `.github/workflows/` and `.github/pr-hygiene/`.
Untrusted text reaches these on every pull request: the body, the branch name,
the filenames, the commit messages and the diff. They are built to survive that
and are audited by `zizmor` and by Scorecard. No workflow here uses
`pull_request_target`; the ones that read a pull request use `pull_request`,
every one of the eighteen declares its permissions at workflow level and every
one of those declarations is deny-all or read-only, all eighteen checkouts run
with `persist-credentials: false`, and the hygiene check has `gh` write the
untrusted values into files that Python reads rather than interpolating any of
them into a shell. Write scopes are granted on the job, and there are four in
the whole of `.github/`: `security-events: write` for CodeQL, for `zizmor` and
for Scorecard, so each can upload its findings, and `id-token: write` for
Scorecard. A route by which a pull request from a fork obtains a writable
token, reaches a secret, or gets code executed in a privileged context is a
real vulnerability and belongs in the advisory channel rather than in a pull
request that demonstrates it.

**Restoring a clone.** The dependency graph is pinned by hash in `uv.lock`, and
`uv sync --locked` refuses a lock that no longer matches `pyproject.toml`:
`toolchain.yml` moves the dependency bound out from under the lock on Linux,
macOS and Windows and fails if the restore succeeds. That is the one
disagreement anything here measures. A way to get a different graph out of that
command than the lock records is a supply-chain finding and I would like it
privately.

## What is not a vulnerability here

**A document from an untrusted source being read at all.** That is the design.
Record 0004 fixes the input as data and not as a program, and JSON is the syntax
because it has no tag, no anchor, no directive and no constructor, so there is
nothing in a document that could name a type even if the loader were wrong.
"This project parses attacker-controlled input" is a description of the project.

**A wrong number.** A field equation or a PPN parameter that disagrees with the
literature is a correctness defect and it is serious, but nothing about it is
confidential, and a public issue gets it read by more people than an advisory
does. Send it there. The exception is a wrong number reached through one of the
surfaces above, which is both things at once.

**A theory the gate refuses, or one it places wrongly.** The admissibility gate
in `src/rechenstrasse/admissibility/` decides which theories this pipeline will
answer for. It is a correctness boundary and not a sandbox: nothing is confined
by it and no attacker is kept out by it. A document it classifies wrongly is a
bug on the tracker rather than an advisory.

**Account takeover, privilege escalation, injection into a database, cross-site
anything, request forgery, SSRF.** There is no account, no privilege level, no
database, no page and no outbound request in this tree. A report naming one of
these is a report about a different program, and I will say so rather than
looking for something here for it to mean.

**Scanner output with no input behind it.** A path in symbolic algebra that no
document can reach is a path no document can reach. If a tool flagged something,
send the document that gets there. Without one there is nothing for me to fix
and nothing for me to confirm.

**An advisory against SymPy itself.** SymPy is the one dependency
`pyproject.toml` declares, and `mpmath` arrives with it: those two are the
runtime group in `THIRD-PARTY-NOTICES.md`. Either project is where a flaw in it
should be reported. Tell me here only if you can reach it through this tree's
surface, and say which document does it. The floor in `pyproject.toml` moves on
that basis.

## What makes a report easy to act on

The smallest document that shows it, the commit from `git rev-parse HEAD`, and
the interpreter build in `.python-version` if you did not restore with
`uv sync --locked`. If the document that triggers it is unpublished work, do not
send it: a document may carry a name, an institution or an address beside the
physics, and a reduced input that fails the same way is better for both of us.

## Warranty

There is none. This is AGPL-3.0, and sections 15 and 16 of [LICENSE](LICENSE)
say so in the terms that bind. Nothing on this page adds one.
