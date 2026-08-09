"""Fuzz the document reader, and replay what fuzzing has already found.

Issue #51. The reader is the one place in this pipeline that eats a file
somebody else wrote, so it is the one place worth fuzzing. Two things live here
and they run in different places, which the issue asks for and which matters
more than it looks:

  the campaign
      Long, and run on a schedule rather than on a change. It mutates the seed
      corpus and calls the target until it has done the rounds it was given,
      and it keeps any input the target did not survive.

  the replay
      Fast and bounded, and run inside `tests` on every change. It walks the
      corpus and the crash directory and requires the target to survive every
      entry. What it prevents is a fixed crash coming back quietly.

The replay fails on an empty corpus rather than passing fast. That is the
failure mode this file is most careful about: a corpus directory that was
emptied, renamed or never reached produces a green result indistinguishable from
a clean one, and a replay that replays nothing is the shape nobody notices.

The campaign is deterministic. It is given a seed and a round count and it
derives every mutation from them, so an input that broke the target on a runner
somewhere is reproduced by running the same two numbers again. That is also what
this file relies on instead of catching everything: a failure of a kind the
recorded list below does not name propagates and ends the run, and the seed and
the round it died on are printed at the start and at the end, so the input is
recoverable without a catch-all around the target. A catch-all is what
`no-catch-all-except` refuses in this directory, and the rule is right: it is
there so that a refusal from a stage cannot be turned into a run that continues.

What is recorded rather than everything, and why the list is named. These are the
kinds a parser fails with, and each one is a defect in the reader rather than in
the input: the reader's contract is that it returns a refusal, so any of these
reaching a caller is the reader crashing.

The network is not reached from here and no fixture is read from outside the
repository, which is what `no-networking-import` and
`no-fixture-outside-the-repository` refuse in this directory. The campaign is the
default environment of record 0009 with nothing relaxed: no display, no
elevation, no network.

    python tools/fuzz.py --rounds 20000
    python tools/fuzz.py --replay
"""

import argparse
import os
import random
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from rechenstrasse.document import reader

# Where the seeds live and where a crash is kept. Both are read by the replay,
# because a crash that has been fixed is exactly the input that has to keep
# being tried.
CORPUS = "fuzz/corpus"
CRASHES = "fuzz/crashes"

# The failures that count as the target crashing. Named rather than caught as a
# group, for the reason in the docstring above. `LookupError` covers a missing
# key and an index off the end, and `ValueError` covers what the loader raises
# and the position index's own refusal to walk on.
RECORDED: tuple[type[BaseException], ...] = (
    ArithmeticError,
    AttributeError,
    LookupError,
    RecursionError,
    TypeError,
    ValueError,
)

# The characters a mutation reaches for. Structure first, because the target is
# a reader of structure and a mutation that only touches letters spends the run
# inside string values.
INTERESTING = '{}[]",:0123456789.-+eEtrufalsn' + chr(92) + chr(10) + chr(9) + chr(32)


@dataclass(frozen=True)
class Crash:
    """One input the target did not survive, and how to get back to it."""

    round: int
    seed_name: str
    failure: str
    text: str


def target(text: str) -> None:
    """The one call being fuzzed.

    A function rather than the expression inline, so what is being fuzzed is a
    thing with a name that the replay and the campaign both use, and neither can
    drift into fuzzing something the other does not.
    """
    reader.read(text)


def entries(root: str) -> list[tuple[str, str]]:
    """Every corpus and crash file in the tree, by path, with its text."""
    found: list[tuple[str, str]] = []
    for directory in (CORPUS, CRASHES):
        full = os.path.join(root, *directory.split("/"))
        if not os.path.isdir(full):
            continue
        for name in sorted(os.listdir(full)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(full, name), encoding="utf-8") as handle:
                found.append((f"{directory}/{name}", handle.read()))
    return sorted(found)


def replay_failures(
    found: Sequence[tuple[str, str]], through: Callable[[str], None]
) -> list[str]:
    """Refusals for one corpus, as `kind: detail` lines.

    A pure function of the entries it is given and the callable it puts them
    through, so both arms can be shown to bite without planting a file in the
    tree or breaking the reader.
    """
    failures: list[str] = []
    if not found:
        failures.append(
            "empty: no corpus entry was reached, so this replay replayed "
            f"nothing. The seeds are {CORPUS} and the crashes are {CRASHES}, and "
            "a directory that was emptied, renamed or never reached gives a "
            "green result that looks exactly like a clean one"
        )
        return failures
    if not any(name.startswith(CORPUS) for name, _ in found):
        failures.append(
            f"empty: {CORPUS} holds no entry, so what was replayed is whatever "
            "fuzzing happened to find and not the corpus this tree keeps"
        )
    for name, text in found:
        try:
            through(text)
        except RECORDED as crash:
            failures.append(
                f"crashed: {name} made the target raise "
                f"{type(crash).__name__}, and an entry in this corpus is an "
                "input the reader has to refuse rather than die on"
            )
    return failures


def mutate(text: str, rng: random.Random) -> str:
    """One input, one edit away from another.

    Seven edits, and the last three are the ones that reach depth. A parser's
    worst inputs are not the ones with a wrong character in them, they are the
    ones that are structurally larger than anything anybody meant to write, and a
    fuzzer that only flips characters never gets there from a small seed. The
    run of one character is the cheapest way in and it is the one that found the
    crash in `fuzz/crashes/`: nothing else in this list turns a document into a
    thousand open brackets inside a few thousand rounds.
    """
    if not text:
        return rng.choice(INTERESTING)
    where = rng.randrange(len(text))
    edit = rng.randrange(7)
    if edit == 0:
        return text[:where] + text[where + 1 :]
    if edit == 1:
        return text[:where] + rng.choice(INTERESTING) + text[where:]
    if edit == 2:
        return text[:where] + rng.choice(INTERESTING) + text[where + 1 :]
    if edit == 3:
        return text[: rng.randrange(len(text))]
    if edit == 4:
        run = rng.choice(INTERESTING) * rng.randrange(2, 4096)
        return text[:where] + run + text[where:]
    cut = min(len(text), where + rng.randrange(1, 8))
    slice_of_it = text[where:cut]
    if edit == 5:
        return text[:where] + slice_of_it * rng.randrange(2, 64) + text[cut:]
    return slice_of_it * rng.randrange(2, 512)


def campaign(
    seeds: Sequence[tuple[str, str]],
    rounds: int,
    seed: int,
    through: Callable[[str], None] = target,
) -> list[Crash]:
    """Mutate the seeds and call the target, `rounds` times, from one seed."""
    rng = random.Random(seed)
    found: list[Crash] = []
    for round_number in range(rounds):
        name, text = seeds[rng.randrange(len(seeds))]
        candidate = mutate(text, rng)
        try:
            through(candidate)
        except RECORDED as crash:
            found.append(
                Crash(
                    round=round_number,
                    seed_name=name,
                    failure=type(crash).__name__,
                    text=candidate,
                )
            )
    return found


def write(found: Iterable[Crash], into: str) -> list[str]:
    """Keep each crash where the replay will pick it up on every change."""
    os.makedirs(into, exist_ok=True)
    written = []
    for crash in found:
        name = f"round-{crash.round}-{crash.failure.lower()}.json"
        path = os.path.join(into, name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(crash.text)
        written.append(path)
    return written


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fuzz the document reader, or replay what fuzzing has found."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
        help="the repository root to read the corpus from",
    )
    parser.add_argument(
        "--replay",
        action="store_true",
        help="walk the corpus once and refuse a crash or an empty corpus",
    )
    parser.add_argument("--rounds", type=int, default=20000)
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="the number every mutation is derived from, so a run reproduces",
    )
    parser.add_argument(
        "--write",
        default=None,
        help="where a crash is kept, defaulting to the crash directory in the tree",
    )
    arguments = parser.parse_args(argv)

    found = entries(arguments.root)
    failures = replay_failures(found, target)
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        print(f"{len(failures)} refusal(s) over {len(found)} entries", file=sys.stderr)
        return 1
    print(f"replayed {len(found)} corpus entries, none of them a crash")
    if arguments.replay:
        return 0

    print(f"fuzzing {arguments.rounds} rounds from seed {arguments.seed}")
    crashes = campaign(found, arguments.rounds, arguments.seed)
    if not crashes:
        print(f"no crash in {arguments.rounds} rounds from seed {arguments.seed}")
        return 0
    into = arguments.write or os.path.join(arguments.root, *CRASHES.split("/"))
    for path in write(crashes, into):
        print(f"kept {path}", file=sys.stderr)
    for crash in crashes:
        print(
            f"round {crash.round} from {crash.seed_name} raised {crash.failure}; "
            f"reproduce with --seed {arguments.seed} --rounds {crash.round + 1}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
