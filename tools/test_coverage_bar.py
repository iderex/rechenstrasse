"""Proof that each arm of the coverage bar bites, and for its own reason.

Issue #49. A bar that cannot fail is a number in a log. Every arm below is
exercised against a report it has to refuse, and the refusal is asserted by the
arm that produced it rather than by its truthiness, because three arms read the
same bytes and a report that measured nothing is also a report under the bar as
far as a boolean is concerned.

The fixtures are reports built here rather than measurements taken here. A
measurement over this tree would move with every change to the suite, so a bar
proved against one would be proved against whatever today happened to be, and
the arm about an empty report could not be reached at all without deleting the
tests it exists to notice the absence of.

The tree's own report is read too, in the one leg that has to be about it: the
surface names files, and a file that left the tree makes the bar quietly cover
less than it says.

    python tools/test_coverage_bar.py
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import coverage_bar

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def a_report(points: dict[str, tuple[int, int]]) -> str:
    """A coverage report holding the files given, each as covered of total.

    The shape `coverage json` writes, cut down to the keys this rule reads.
    Branches are folded into the totals here, because the rule adds the two and
    a fixture that separated them would be testing arithmetic this file made up.
    """
    files = {
        name: {
            "summary": {
                "covered_lines": covered,
                "num_statements": total,
                "covered_branches": 0,
                "num_branches": 0,
                "percent_covered": 100.0 * covered / total if total else 100.0,
            }
        }
        for name, (covered, total) in points.items()
    }
    return json.dumps({"files": files, "totals": {"percent_covered": 100.0}})


def every_surface_file(covered: int, total: int) -> dict[str, tuple[int, int]]:
    return {entry.path: (covered, total) for entry in coverage_bar.SURFACE}


def kinds(found: list[str]) -> list[str]:
    return sorted({reason.split(":", 1)[0] for reason in found})


class TheBarItself(unittest.TestCase):
    def test_a_report_above_the_bar_is_accepted(self) -> None:
        # The near miss for every arm below. One point above the bar has to
        # pass, or the arms are refusing the wrong thing.
        self.assertEqual(
            [], coverage_bar.failures(a_report(every_surface_file(91, 100)), 90.0)
        )

    def test_a_report_one_point_under_the_bar_is_refused(self) -> None:
        # The one-point difference is the whole assertion. A fixture at zero
        # would prove the code runs rather than that the bar is where it says.
        found = coverage_bar.failures(a_report(every_surface_file(89, 100)), 90.0)
        self.assertEqual(["below"], kinds(found))

    def test_a_report_exactly_on_the_bar_is_accepted(self) -> None:
        # Which side the boundary falls on is a decision, and an undecided one
        # is where a bar drifts by a point per change.
        self.assertEqual(
            [], coverage_bar.failures(a_report(every_surface_file(90, 100)), 90.0)
        )

    def test_bytes_that_are_not_a_report_are_refused(self) -> None:
        self.assertEqual(["unreadable"], kinds(coverage_bar.failures("{", 90.0)))

    def test_a_document_without_a_file_table_is_refused(self) -> None:
        # Readable JSON and not a coverage report, which is what a wrong path to
        # a different tool's output looks like.
        found = coverage_bar.failures(json.dumps({"totals": {}}), 90.0)
        self.assertEqual(["unreadable"], kinds(found))

    def test_a_report_that_measured_nothing_is_refused(self) -> None:
        # Not a division by zero and not a pass. This is the state a renamed
        # module or a measurement over nothing arrives in.
        found = coverage_bar.failures(a_report(every_surface_file(0, 0)), 90.0)
        self.assertIn("empty", kinds(found))

    def test_a_report_holding_none_of_the_surface_is_refused(self) -> None:
        found = coverage_bar.failures(
            a_report({"src/rechenstrasse/cli.py": (10, 10)}), 90.0
        )
        self.assertEqual(["dangling", "empty"], kinds(found))

    def test_a_surface_entry_the_report_lost_is_refused(self) -> None:
        # The arm that catches a surface file which moved. Everything else in
        # the report is above the bar, so nothing but this says anything.
        points = every_surface_file(100, 100)
        points.pop(coverage_bar.SURFACE[0].path)
        self.assertEqual(
            ["dangling"], kinds(coverage_bar.failures(a_report(points), 90.0))
        )

    def test_the_surface_is_not_empty(self) -> None:
        # A guard whose subject went away is one that stopped working. An empty
        # surface would make every leg above pass by having nothing to measure.
        self.assertNotEqual((), coverage_bar.SURFACE)


class TheTreeAsItStands(unittest.TestCase):
    """The one leg that has to read a real report rather than a built one."""

    def setUp(self) -> None:
        self.report = os.path.join(ROOT, ".coverage.json")
        if not os.path.isfile(self.report):
            self.skipTest(
                f"no coverage report at {self.report}. This leg reads the "
                "measurement of this tree and there is none here, so it decides "
                "nothing rather than passing. `coverage run -m pytest` and "
                "`coverage json -o .coverage.json` produce one"
            )

    def test_every_surface_file_is_in_the_measurement(self) -> None:
        with open(self.report, encoding="utf-8") as handle:
            report = coverage_bar.load(handle.read())
        self.assertIsNotNone(report)
        assert report is not None
        self.assertEqual([], coverage_bar.missing(report, coverage_bar.SURFACE))

    def test_the_command_exits_zero_on_the_tree(self) -> None:
        self.assertEqual(0, coverage_bar.main(["--report", self.report, "--bar", "90"]))

    def test_the_command_exits_one_on_a_report_that_is_not_there(self) -> None:
        absent = os.path.join(ROOT, ".coverage.json.that.is.not.here")
        self.assertEqual(1, coverage_bar.main(["--report", absent]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
