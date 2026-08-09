"""The seed corpus replay of issue #51, and the two arms that make it worth running.

The replay is the half of that issue that runs on every change. It walks the
corpus and the crash directory and requires the reader to survive every entry,
so a crash that has been fixed cannot come back quietly.

The failure this file is most careful about is not a crash. It is a replay that
replayed nothing. An emptied corpus, a renamed directory or a path that stopped
resolving all produce a fast green result indistinguishable from a clean one, and
that is asserted here as its own leg rather than assumed from the entries being
found today.

The campaign is not run here. It is long by design and it belongs on a schedule,
in `.github/workflows/fuzz.yml`, which is where issue #51 puts it and where
record 0009 puts work nobody would sit through on every change. What is exercised
here is that the campaign's machinery works on a handful of rounds, because a
scheduled job whose target stopped building reports success on most harnesses.
"""

import os
import random
import sys
from pathlib import Path

from rechenstrasse.document import reader

ROOT = Path(__file__).resolve().parents[1]

# The harness is a tool and not part of the installed package, so it is reached
# the way the other tools' proofs reach theirs, by putting the directory on the
# path and importing the module by its own name. Importing it as `tools.fuzz`
# instead would give one file two module names, which the type checker refuses.
sys.path.insert(0, os.path.join(str(ROOT), "tools"))

import fuzz  # noqa: E402


def corpus() -> list[tuple[str, str]]:
    return fuzz.entries(str(ROOT))


def test_the_reader_survives_every_entry_in_the_corpus() -> None:
    """The replay itself, which is what runs on every change."""
    found = corpus()
    assert fuzz.replay_failures(found, fuzz.target) == []


def test_the_corpus_holds_seeds_and_the_crashes_found_so_far() -> None:
    """Both directories are reached, asserted by name rather than by a count.

    A count would go stale the day somebody adds a seed. What matters is that
    neither directory is the one that silently stopped being read.
    """
    names = {name for name, _ in corpus()}
    assert any(name.startswith(fuzz.CORPUS) for name in names)
    assert any(name.startswith(fuzz.CRASHES) for name in names)


def test_an_empty_corpus_fails_the_replay_rather_than_passing_fast() -> None:
    """The arm the issue puts most weight on, on the empty list itself."""
    failures = fuzz.replay_failures([], fuzz.target)
    assert len(failures) == 1
    assert failures[0].startswith("empty:")


def test_a_corpus_of_crashes_and_no_seeds_fails_too() -> None:
    """The same failure arriving by a path change rather than by deletion.

    A replay reading only what fuzzing happened to find is not the corpus this
    tree keeps, and it is the shape a moved seed directory takes: entries are
    still found, so a check that only asked whether the list was empty passes.
    """
    only_crashes = [(f"{fuzz.CRASHES}/something.json", "{}")]
    failures = fuzz.replay_failures(only_crashes, fuzz.target)
    assert len(failures) == 1
    assert failures[0].startswith("empty:")


def test_the_replay_reports_an_entry_the_target_did_not_survive() -> None:
    """The other arm, on a target that raises rather than on a broken reader."""

    def raises(text: str) -> None:
        raise ValueError("this input was not survived")

    failures = fuzz.replay_failures([("fuzz/corpus/one.json", "{}")], raises)
    assert len(failures) == 1
    assert failures[0].startswith("crashed: fuzz/corpus/one.json")
    assert "ValueError" in failures[0]


def test_the_replay_lets_a_failure_it_does_not_name_through() -> None:
    """What the named list costs, asserted rather than left to be discovered.

    A failure of a kind `RECORDED` does not name is not reported as a crash, it
    ends the run. That is the trade this file makes instead of a catch-all, and
    a reader of a green replay should know which failures it was watching for.
    """

    def interrupts(text: str) -> None:
        raise KeyboardInterrupt

    try:
        fuzz.replay_failures([("fuzz/corpus/one.json", "{}")], interrupts)
    except KeyboardInterrupt:
        return
    raise AssertionError("the replay swallowed a failure it does not name")


def test_the_campaign_produces_inputs_and_finds_nothing_on_a_healthy_target() -> None:
    """A few rounds of the real thing, so the machinery cannot rot unnoticed.

    Short on purpose. What this asserts is that the campaign reaches the target
    with mutated input and reports no crash on the reader as it stands, not that
    the reader is free of them, which is what the scheduled run is for.
    """
    assert fuzz.campaign(corpus(), rounds=200, seed=7) == []


def test_the_campaign_reports_a_target_that_crashes() -> None:
    """The proof that a crash would be kept rather than counted as a round."""

    def raises(text: str) -> None:
        raise RecursionError("over the edge")

    found = fuzz.campaign(corpus(), rounds=3, seed=7, through=raises)
    assert [crash.failure for crash in found] == ["RecursionError"] * 3
    assert found[0].round == 0
    assert found[0].seed_name.startswith("fuzz/")


def test_the_campaign_is_the_same_run_twice_from_one_seed() -> None:
    """What stands in for keeping every input: a round number and a seed."""
    rng = random.Random(11)
    once = [fuzz.mutate('{\n  "a": 1\n}\n', rng) for _ in range(50)]
    rng = random.Random(11)
    again = [fuzz.mutate('{\n  "a": 1\n}\n', rng) for _ in range(50)]
    assert once == again
    assert len(set(once)) > 1


def test_a_mutation_of_nothing_is_still_something() -> None:
    """The one input with no position to edit, which is where an index error lives."""
    assert fuzz.mutate("", random.Random(3)) in fuzz.INTERESTING


def test_the_recursion_crash_is_refused_and_names_where_it_gave_up() -> None:
    """The first crash this corpus carries, as the refusal that replaced it.

    Kept as the input the campaign produced rather than as a tidied version of
    it, because the fixture exists to prove that this exact input cannot come
    back.
    """
    text = (ROOT / "fuzz/crashes/recursion-from-a-run-of-open-brackets.json").read_text(
        encoding="utf-8"
    )
    action, found = reader.read(text)
    assert action is None
    assert [refusal.rule for refusal in found] == ["too-deeply-nested"]
    assert found[0].at.line >= 1
    assert found[0].named == str(reader.NESTING_LIMIT)


def test_the_duplicate_key_crash_is_refused_and_names_the_key() -> None:
    """The second one. It is a crash in the position index and a defect in the reading.

    The loader keeps the last of two members under one key and says nothing, so
    the document reads as though it had said one thing, which is what record
    0004 rules out for a key nobody admits and is worse for a key everybody does.
    """
    text = (ROOT / "fuzz/crashes/a-key-written-twice.json").read_text(encoding="utf-8")
    action, found = reader.read(text)
    assert action is None
    assert {refusal.rule for refusal in found} == {"key-written-twice"}
