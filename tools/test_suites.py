"""Proof that the disclosure of what a run did not run fails closed both ways.

Issue #15. The value of the list in `tools/suites.py` is entirely in its being
true on the day somebody reads a green run, so the two ways it can stop being
true are what this suite is about: an entry describing a suite that is no longer
there, and a suite in the tree that no entry describes.

Every refusal is asserted by its kind and never by its truthiness. The two kinds
read the same tree, and a fixture that trips both would pass a test that only
asks whether something was refused.

Each refused tree is the real tree with exactly one file added or removed, and
each one is paired with the near miss: the same edit a contributor would
actually make that must not be refused. Adding a test under `tests/` is the
common case and is not a disclosure question at all; adding one under `tools/`,
or marking one slow, is the same keystroke with the opposite answer.

Standard library only, and no network.

    python tools/test_suites.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import suites

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# A test file with nothing remarkable in it. Every tree below is the real tree
# with this file added at one path or another, so a fixture's only defect is
# where it sits and what it carries.
PLAIN_TEST = '"""A test."""\n\n\ndef test_something() -> None:\n    assert True\n'

SLOW_TEST = (
    '"""A test that walks the tree."""\n\nimport pytest\n\n\n'
    "@pytest.mark.slow\ndef test_something_slow() -> None:\n    assert True\n"
)


def assert_kind(case: unittest.TestCase, failures: list[str], kind: str) -> None:
    """Exactly one refusal, and it is of the kind named."""
    case.assertEqual(1, len(failures), failures)
    case.assertTrue(
        failures[0].startswith(f"{kind}: "),
        f"expected a {kind} refusal, got {failures[0]!r}",
    )


class TheTreeAsItStands(unittest.TestCase):
    def files(self) -> list[tuple[str, str]]:
        found = suites.test_files(ROOT)
        self.assertNotEqual([], found)
        return found

    def test_the_disclosure_matches_the_tree(self) -> None:
        self.assertEqual([], suites.failures(self.files()))

    def test_the_command_exits_zero_on_the_tree(self) -> None:
        self.assertEqual(0, suites.main([ROOT]))

    def test_the_command_exits_one_on_a_root_with_no_tests(self) -> None:
        # A wrong root must not read as a tree whose disclosure is in order.
        # Without this the check passes on any typo in the workflow, and the
        # list it prints is then a list about nothing. The directory chosen
        # holds no file that reads as a suite, so the one refusal is the empty
        # walk and not a disclosure that drifted.
        self.assertEqual(1, suites.main([os.path.join(ROOT, "docs")]))

    def test_every_entry_is_printed_with_its_command(self) -> None:
        # An entry that exists in the data and not in the output discloses
        # nothing to the reader the disclosure is for.
        printed = suites.report()
        for suite in suites.SUITES:
            self.assertIn(suite.name, printed)
            self.assertIn(suite.command, printed)
            self.assertIn(suite.because, printed)
        for path, reason in suites.NOT_A_SUITE:
            self.assertIn(path, printed)
            self.assertIn(reason, printed)


class ADanglingEntry(unittest.TestCase):
    def tree_without(self, victim: str) -> list[tuple[str, str]]:
        found = [
            (path, text) for path, text in suites.test_files(ROOT) if path != victim
        ]
        self.assertNotIn(victim, [path for path, _ in found])
        return found

    def test_an_entry_whose_file_left_the_tree_is_refused(self) -> None:
        victim = next(path for suite in suites.SUITES for path in suite.paths)
        assert_kind(self, suites.failures(self.tree_without(victim)), "dangling")

    def test_an_exemption_whose_file_left_the_tree_is_refused(self) -> None:
        victim = suites.NOT_A_SUITE[0][0]
        assert_kind(self, suites.failures(self.tree_without(victim)), "dangling")

    def test_an_entry_whose_covered_directory_emptied_is_refused(self) -> None:
        # A prefix costs nothing to keep and is the entry least likely to be
        # noticed once the directory under it goes away, because no single file
        # name in it ever appears here.
        prefix = next(prefix for suite in suites.SUITES for prefix in suite.covers)
        emptied = [
            (path, text)
            for path, text in suites.test_files(ROOT)
            if not path.startswith(prefix)
        ]
        assert_kind(self, suites.failures(emptied), "dangling")

    def test_a_tree_with_no_tests_at_all_is_refused_rather_than_accepted(self) -> None:
        # Not one refusal but several, and the point is that it is not zero: an
        # empty input is the shape a wrong root arrives in, and the disclosure
        # has nothing to say about it truthfully.
        self.assertNotEqual([], suites.failures([]))


class AnUndisclosedSuite(unittest.TestCase):
    def tree_with(self, path: str, text: str) -> list[tuple[str, str]]:
        found = suites.test_files(ROOT)
        self.assertNotIn(path, [existing for existing, _ in found])
        return [*found, (path, text)]

    def test_a_suite_outside_the_default_run_is_refused(self) -> None:
        failures = suites.failures(self.tree_with("tools/test_export.py", PLAIN_TEST))
        assert_kind(self, failures, "undisclosed")

    def test_a_test_inside_the_default_run_is_not_refused(self) -> None:
        # The near miss. This is the common change and it needs no entry,
        # because the default run reads it.
        self.assertEqual(
            [],
            suites.failures(
                self.tree_with("tests/rechenstrasse/test_variation.py", PLAIN_TEST)
            ),
        )

    def test_a_file_added_under_a_covered_directory_is_not_refused(self) -> None:
        # The reason a prefix exists. A harness that grows a case must not have
        # to be re-declared here, or the declaration becomes the thing people
        # work around.
        prefix = next(prefix for suite in suites.SUITES for prefix in suite.covers)
        self.assertEqual(
            [],
            suites.failures(
                self.tree_with(f"{prefix}test_one_more_case.py", PLAIN_TEST)
            ),
        )

    def test_a_file_beside_a_covered_directory_is_still_refused(self) -> None:
        # The near miss for the prefix. A prefix covers what is under it and not
        # what merely starts with the same letters, which is the mistake a
        # directory renamed by one character makes.
        prefix = next(prefix for suite in suites.SUITES for prefix in suite.covers)
        beside = f"{prefix.rstrip('/')}_elsewhere/test_case.py"
        assert_kind(
            self, suites.failures(self.tree_with(beside, PLAIN_TEST)), "undisclosed"
        )

    def test_a_slow_test_inside_the_default_run_is_refused(self) -> None:
        # The same file as the near miss above with the marker on it, which is
        # the one keystroke that takes it out of the default run.
        failures = suites.failures(
            self.tree_with("tests/rechenstrasse/test_variation.py", SLOW_TEST)
        )
        assert_kind(self, failures, "undisclosed")

    def test_a_file_that_is_not_named_like_a_test_is_not_read(self) -> None:
        # The walk decides what holds tests by the file name, and a helper
        # beside a suite is not one. This is the bound the docstring of
        # tools/suites.py states, asserted rather than assumed: a suite written
        # in a file called something else is outside this check entirely.
        self.assertFalse(suites.is_test_file("tools/export.py"))
        self.assertTrue(suites.is_test_file("tools/test_export.py"))
        self.assertTrue(suites.is_test_file("fixtures/only_a_failing_test.py"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
