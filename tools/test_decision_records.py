"""Proof that each arm of the decision record rule bites, and for its own reason.

Issue #1. Every arm is tested twice: once against a file it refuses, and once
against the nearest file it must not refuse. The near miss is the point. An arm
proven only against something obviously wrong proves that the code runs, not
that the rule holds.

The refusing fixtures are built from one complete record by taking exactly one
thing away, so a fixture's only defect is the one under test. A fixture written
out by hand drifts from the valid one and then proves whichever difference the
writer happened to introduce.

A refusal is asserted by the arm that produced it and never by its truthiness.
Four arms read the same directory, and a file with a bad name is also a file
whose sections nobody checked, so a test that only asks whether something was
refused passes with the arm it is about deleted.

Standard library only, and no network.

    python tools/test_decision_records.py
"""

import os
import sys
import unittest
from collections.abc import Iterable, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import decision_records

VALID = """# 0031. A decision that was made

Ordered by issue #31.

## Question

What was being decided.

## Answer

What holds now.

## Reasons

Why this and not the other one, which cost more.

## Ruled out

The thing this answer forbids.

## Reopened when

The measurement that makes this worth arguing again.
"""


def without(section: str) -> str:
    """The valid record with one section heading and its body removed."""
    lines = VALID.splitlines(keepends=True)
    kept = []
    dropping = False
    for line in lines:
        if line.rstrip() == section:
            dropping = True
            continue
        if dropping and line.startswith("## "):
            dropping = False
        if not dropping:
            kept.append(line)
    return "".join(kept)


def emptied(section: str) -> str:
    """The valid record with one section's body removed and its heading kept."""
    lines = VALID.splitlines(keepends=True)
    kept = []
    dropping = False
    for line in lines:
        if line.rstrip() == section:
            kept.append(line)
            dropping = True
            continue
        if dropping and line.startswith("## "):
            dropping = False
        if not dropping:
            kept.append(line)
    return "".join(kept)


def arms(failures: Iterable[str]) -> list[str]:
    return sorted(failure.split(":", 1)[0] for failure in failures)


def assert_arm(case: unittest.TestCase, failures: Sequence[str], arm: str) -> None:
    """The refusal came from this arm, rather than from something being wrong."""
    case.assertIn(arm, arms(failures), f"expected {arm}, got {failures}")


class TheFixturesThemselves(unittest.TestCase):
    def test_the_valid_record_is_refused_by_nothing(self) -> None:
        self.assertEqual([], decision_records.failures([("0031-a-record.md", VALID)]))

    def test_removing_a_section_removes_only_that_section(self) -> None:
        text = without("## Ruled out")
        self.assertNotIn("## Ruled out", text)
        self.assertIn("## Reopened when", text)
        self.assertIn("The measurement that makes this worth arguing again.", text)

    def test_emptying_a_section_keeps_its_heading(self) -> None:
        text = emptied("## Reopened when")
        self.assertIn("## Reopened when", text)
        self.assertNotIn("The measurement that makes this worth arguing again.", text)


class EveryRequiredSectionIsRequired(unittest.TestCase):
    def test_a_record_missing_one_section_is_refused_for_each_of_the_five(self) -> None:
        # The whole point of the rule, run once per section rather than once,
        # because a checker that reads four of the five headings passes a test
        # that only removes the one it happens to read.
        for section in decision_records.REQUIRED_SECTIONS:
            with self.subTest(section=section):
                failures = decision_records.failures(
                    [("0031-a-record.md", without(section))]
                )
                assert_arm(self, failures, "section-missing")
                self.assertEqual(1, len(failures), failures)
                self.assertIn(section, failures[0])

    def test_a_record_with_all_five_is_not_refused(self) -> None:
        self.assertEqual([], decision_records.failures([("0031-a-record.md", VALID)]))

    def test_a_sixth_section_is_not_refused(self) -> None:
        # A superseding record carries `## Supersedes`. The rule must not
        # mistake an extra section for a defect.
        text = VALID + "\n## Supersedes\n\nRecord 0007.\n"
        self.assertEqual([], decision_records.failures([("0031-a-record.md", text)]))

    def test_a_heading_that_differs_only_in_case_is_refused(self) -> None:
        # The near miss for this arm: the writer typed the heading, it looks
        # right in a rendered page, and no route reads it.
        text = VALID.replace("## Reopened when", "## Reopened When")
        failures = decision_records.failures([("0031-a-record.md", text)])
        assert_arm(self, failures, "section-missing")

    def test_a_heading_at_a_deeper_level_is_refused(self) -> None:
        text = VALID.replace("## Ruled out", "### Ruled out")
        failures = decision_records.failures([("0031-a-record.md", text)])
        assert_arm(self, failures, "section-missing")


class AHeadingWithNothingUnderItIsNotASection(unittest.TestCase):
    def test_an_empty_section_is_refused_for_each_of_the_five(self) -> None:
        for section in decision_records.REQUIRED_SECTIONS:
            with self.subTest(section=section):
                failures = decision_records.failures(
                    [("0031-a-record.md", emptied(section))]
                )
                assert_arm(self, failures, "section-empty")
                self.assertEqual(1, len(failures), failures)

    def test_a_section_holding_one_word_is_not_refused(self) -> None:
        # The near miss. A thin section is a review problem, not a rule
        # problem, and this arm must not start having opinions about length.
        text = VALID.replace(
            "The measurement that makes this worth arguing again.", "Never."
        )
        self.assertEqual([], decision_records.failures([("0031-a-record.md", text)]))

    def test_a_section_holding_only_blank_lines_is_refused(self) -> None:
        text = VALID.replace(
            "The measurement that makes this worth arguing again.", "   \n\t\n"
        )
        failures = decision_records.failures([("0031-a-record.md", text)])
        assert_arm(self, failures, "section-empty")


class TheFilenameCarriesTheIssueNumber(unittest.TestCase):
    def test_a_name_with_three_digits_is_refused(self) -> None:
        failures = decision_records.failures([("031-a-record.md", VALID)])
        assert_arm(self, failures, "filename-shape")

    def test_a_name_with_four_digits_is_not_refused(self) -> None:
        self.assertEqual([], decision_records.failures([("0031-a-record.md", VALID)]))

    def test_a_name_with_no_number_is_refused(self) -> None:
        failures = decision_records.failures([("a-record.md", VALID)])
        assert_arm(self, failures, "filename-shape")

    def test_an_uppercase_slug_is_refused(self) -> None:
        failures = decision_records.failures([("0031-A-Record.md", VALID)])
        assert_arm(self, failures, "filename-shape")

    def test_a_slug_with_an_underscore_is_refused(self) -> None:
        failures = decision_records.failures([("0031_a_record.md", VALID)])
        assert_arm(self, failures, "filename-shape")

    def test_a_one_word_slug_is_not_refused(self) -> None:
        self.assertEqual([], decision_records.failures([("0031-record.md", VALID)]))


class ANumberIsNeverReused(unittest.TestCase):
    def test_two_records_carrying_one_number_are_refused(self) -> None:
        failures = decision_records.failures(
            [("0031-a-record.md", VALID), ("0031-another-record.md", VALID)]
        )
        assert_arm(self, failures, "number-reused")

    def test_two_records_carrying_two_numbers_are_not_refused(self) -> None:
        self.assertEqual(
            [],
            decision_records.failures(
                [("0031-a-record.md", VALID), ("0032-another-record.md", VALID)]
            ),
        )

    def test_the_refusal_names_both_files(self) -> None:
        failures = decision_records.failures(
            [("0031-a-record.md", VALID), ("0031-another-record.md", VALID)]
        )
        reused = [f for f in failures if f.startswith("number-reused")]
        self.assertEqual(1, len(reused), failures)
        self.assertIn("0031-a-record.md", reused[0])
        self.assertIn("0031-another-record.md", reused[0])


class TheDirectoryInThisTree(unittest.TestCase):
    def directory(self) -> str:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(root, "docs", "decisions")

    def test_every_record_in_the_tree_is_in_shape(self) -> None:
        records = decision_records.read_directory(self.directory())
        self.assertNotEqual([], records)
        self.assertEqual([], decision_records.failures(records))

    def test_the_template_carries_the_headings_the_checker_requires(self) -> None:
        # The template is what a writer copies and the tuple is what the
        # checker reads. Held to each other here, so a heading renamed in one
        # place cannot sit quietly against the other.
        path = os.path.join(self.directory(), "0000-template.md")
        with open(path, encoding="utf-8") as handle:
            bodies = decision_records.section_bodies(handle.read())
        for heading in decision_records.REQUIRED_SECTIONS:
            self.assertIn(heading, bodies)
            self.assertNotEqual("", bodies[heading])

    def test_the_command_exits_zero_on_the_tree(self) -> None:
        self.assertEqual(0, decision_records.main([self.directory()]))

    def test_the_command_exits_one_on_a_directory_with_no_records(self) -> None:
        # A wrong path must not read as a clean run. Without this the check
        # passes on any typo in the workflow.
        self.assertEqual(1, decision_records.main([os.path.dirname(__file__)]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
