"""Proof that each arm of the third party notice rule bites, and for its own reason.

Issue #57. The notice in the tree is generated, and the only thing standing
between it and a document that quietly stopped describing this tree is the
comparison in `third_party_notices.differences`. Every arm below is exercised
against something it has to refuse, and the refusal is asserted by the arm that
produced it rather than by its truthiness, because four arms read the same two
inputs and a test that only asks whether something was refused passes with the
arm it is about deleted.

One test is about a platform rather than a mistake. A lock holds distributions
installed on one operating system and not on another, so the check verifies the
terms column only where this environment holds the distribution. That is a hole
by design, and the test asserts it is exactly that shape: an absent distribution
is not verified and is not refused, and its row is still required.

    python tools/test_third_party_notices.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import third_party_notices as notices

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOCK = os.path.join(ROOT, "uv.lock")
NOTICE = os.path.join(ROOT, "THIRD-PARTY-NOTICES.md")


def read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def kinds(found: list[str]) -> list[str]:
    """The identifier at the start of each refusal, which is what an arm is."""
    return sorted({reason.split(":", 1)[0] for reason in found})


class TheTreeAsItStands(unittest.TestCase):
    def setUp(self) -> None:
        self.document = notices.lock(read(LOCK))
        self.rows = notices.rows(self.document)
        self.terms = notices.installed(row.name for row in self.rows)

    def test_the_notice_is_what_the_lock_and_this_environment_say(self) -> None:
        self.assertEqual([], notices.differences(self.rows, self.terms, read(NOTICE)))

    def test_the_command_exits_zero_on_the_tree(self) -> None:
        self.assertEqual(0, notices.main(["--lock", LOCK, "--check", NOTICE]))

    def test_the_lock_holds_something_to_report(self) -> None:
        # A guard that passes because its subject went away is one that stopped
        # working. An empty lock would satisfy every arm above by having nothing
        # to compare.
        self.assertNotEqual([], self.rows)

    def test_the_project_itself_is_not_a_third_party(self) -> None:
        self.assertNotIn(notices.THIS_PROJECT, {row.name for row in self.rows})

    def test_every_distribution_in_the_lock_is_placed(self) -> None:
        # A distribution in neither group is one the notice never mentions,
        # which is the failure this file exists against rather than an omission.
        listed = self.document["package"]
        assert isinstance(listed, list)
        in_lock = {
            entry["name"] for entry in listed if entry["name"] != notices.THIS_PROJECT
        }
        self.assertEqual(in_lock, {row.name for row in self.rows})

    def test_the_runtime_graph_and_the_development_group_are_kept_apart(self) -> None:
        placed = {row.name: row.group for row in self.rows}
        listed = self.document["package"]
        assert isinstance(listed, list)
        project = next(
            entry for entry in listed if entry["name"] == notices.THIS_PROJECT
        )
        declared = [member["name"] for member in project["dependencies"]]
        self.assertNotEqual([], declared)
        for name in declared:
            self.assertEqual(notices.RUNTIME, placed[name])
        development = {
            name for name, group in placed.items() if group == notices.DEVELOPMENT
        }
        self.assertNotEqual(set(), development)
        self.assertTrue(set(declared).isdisjoint(development))


class ANoticeThatDrifted(unittest.TestCase):
    """Each arm against a notice one edit away from the one in the tree.

    The base is the tracked notice rather than a freshly rendered one, and that
    is not a convenience. Rendering needs terms for every row, which an
    environment missing a platform-conditional distribution cannot supply, so a
    suite that rendered its own base would be a suite that only runs on one
    operating system. Planting into the file that is actually in the tree is
    also the closer fixture: it is the document a person edits by hand.
    """

    def setUp(self) -> None:
        self.document = notices.lock(read(LOCK))
        self.rows = notices.rows(self.document)
        self.terms = notices.installed(row.name for row in self.rows)
        self.written = read(NOTICE)

    def refusals(self, planted: str) -> list[str]:
        return notices.differences(self.rows, self.terms, planted)

    def test_a_version_that_moved_is_refused(self) -> None:
        # The drift that actually happens, and it is one character.
        victim = self.rows[0]
        planted = self.written.replace(
            f"| `{victim.name}` | {victim.version} |",
            f"| `{victim.name}` | {victim.version}1 |",
        )
        self.assertNotEqual(self.written, planted)
        self.assertEqual(["version"], kinds(self.refusals(planted)))

    def test_a_row_that_went_away_is_refused(self) -> None:
        victim = self.rows[0]
        planted = "\n".join(
            line for line in self.written.splitlines() if f"`{victim.name}`" not in line
        )
        self.assertNotEqual(self.written, planted)
        self.assertEqual(["group", "missing"], kinds(self.refusals(planted)))

    def test_a_row_the_lock_does_not_hold_is_refused(self) -> None:
        # The opposite direction, and the one a reader cannot catch: a row
        # naming something this tree does not install reads exactly like a row
        # that does.
        planted = self.written.replace(
            "| --- | --- | --- |",
            "| --- | --- | --- |\n| `a-distribution-nobody-installs` | 1.0 | MIT |",
            1,
        )
        self.assertNotEqual(self.written, planted)
        self.assertEqual(["stale"], kinds(self.refusals(planted)))

    def test_terms_that_contradict_the_environment_are_refused(self) -> None:
        victim = next(row for row in self.rows if row.name in self.terms)
        planted = self.written.replace(
            f"| `{victim.name}` | {victim.version} | {self.terms[victim.name]} |",
            f"| `{victim.name}` | {victim.version} | Public domain |",
        )
        self.assertNotEqual(self.written, planted)
        self.assertEqual(["terms"], kinds(self.refusals(planted)))

    def test_a_distribution_under_the_wrong_heading_is_refused(self) -> None:
        # The one a row comparison alone would not see. A distribution that
        # moved from the development group into the runtime graph changes what
        # an installed copy carries, and its row is identical either way. Moved
        # on the lock side rather than in the document, because the assertion is
        # that the two disagreeing is refused and the direction does not matter.
        moved = [
            notices.Row(row.name, row.version, notices.RUNTIME)
            if row.group == notices.DEVELOPMENT
            else row
            for row in self.rows
        ]
        self.assertNotEqual(self.rows, moved)
        found = notices.differences(moved, self.terms, self.written)
        self.assertEqual(["group"], kinds(found))

    def test_a_distribution_this_environment_lacks_is_unverified(self) -> None:
        absent = self.rows[0].name
        thinner = {name: value for name, value in self.terms.items() if name != absent}
        self.assertEqual([], notices.differences(self.rows, thinner, self.written))
        # And the row is still required, so the hole is in the terms column only.
        without_the_row = "\n".join(
            line for line in self.written.splitlines() if f"`{absent}`" not in line
        )
        self.assertIn(
            "missing", kinds(notices.differences(self.rows, thinner, without_the_row))
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
