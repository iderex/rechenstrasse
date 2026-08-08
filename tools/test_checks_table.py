"""Proof that each arm of the checks-table rule bites, and for its own reason.

Issue #86. Every arm is tested twice: once against something it refuses, and
once against the nearest thing it must not refuse. The near miss is the point.
An arm proven only against something obviously wrong proves that the code runs,
not that the rule holds.

A refusal is asserted by the arm that produced it and never by its truthiness.
Several arms read the same two inputs, and a row naming a check nothing produces
is also a table one check short, so a test that only asks whether something was
refused passes with the arm it is about deleted. The identifier at the start of
each line is what makes each arm provable on its own.

The register of checks that come from outside this tree is exercised through the
real tuple rather than a substitute, so an entry added to it without a row, or
kept after a workflow starts producing the check, reds this suite.

    python tools/test_checks_table.py
"""

import os
import sys
import unittest
from collections.abc import Iterable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import checks_table

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# A workflow that produces one check on a pull request, and the smallest thing
# that is still one. Every fixture below is this file with one thing changed, so
# a fixture's only defect is the one under test.
VALID_WORKFLOW = """
name: Example
on:
  push:
    branches: [main]
  pull_request:
    branches: ["**"]
jobs:
  example:
    name: an example check
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""

VALID_TABLE = """# A document

| On the pull request | In a clone |
| --- | --- |
| `an example check` | `true` |
"""


def kinds(found: Iterable[str]) -> list[str]:
    """The arm identifier of every refusal, which is what each test asserts."""
    return sorted({line.split(":", 1)[0] for line in found})


def one(text: str) -> list[tuple[str, str]]:
    return [(".github/workflows/example.yml", text)]


class TheTableIsRead(unittest.TestCase):
    def test_a_row_is_read_out_of_the_column_the_rule_anchors_on(self) -> None:
        rows, found = checks_table.table_names(VALID_TABLE)
        self.assertEqual(["an example check"], rows)
        self.assertEqual([], found)

    def test_a_document_without_that_column_is_refused_rather_than_empty(self) -> None:
        # The near miss: the same table with the first column renamed. Without
        # this arm a renamed heading reads as a table with no rows, and a table
        # with no rows refuses nothing.
        renamed = VALID_TABLE.replace(checks_table.FIRST_COLUMN, "Check")
        rows, found = checks_table.table_names(renamed)
        self.assertEqual([], rows)
        self.assertEqual(["no-table"], kinds(found))

    def test_a_row_whose_name_is_not_backticked_is_refused(self) -> None:
        loose = VALID_TABLE.replace("`an example check`", "an example check")
        rows, found = checks_table.table_names(loose)
        self.assertEqual([], rows)
        self.assertEqual(["unreadable-row"], kinds(found))

    def test_a_table_elsewhere_in_the_document_is_not_read_as_this_one(self) -> None:
        other = VALID_TABLE + "\n| Something | Else |\n| --- | --- |\n| a | b |\n"
        rows, found = checks_table.table_names(other)
        self.assertEqual(["an example check"], rows)
        self.assertEqual([], found)


class TheNamesComeFromTheWorkflows(unittest.TestCase):
    def test_a_named_job_gives_its_name(self) -> None:
        produced, found = checks_table.workflow_checks(one(VALID_WORKFLOW))
        self.assertEqual([], found)
        self.assertEqual(
            {"an example check": ".github/workflows/example.yml"}, produced
        )

    def test_a_job_without_a_name_gives_its_id(self) -> None:
        # This is not hypothetical. The dependency review job in this tree
        # carries no name, and the check on the pull request is its id.
        unnamed = VALID_WORKFLOW.replace("    name: an example check\n", "")
        produced, found = checks_table.workflow_checks(one(unnamed))
        self.assertEqual([], found)
        self.assertEqual(["example"], sorted(produced))

    def test_a_workflow_with_no_pull_request_trigger_produces_nothing(self) -> None:
        # The near miss for every arm below: `Scorecard analysis` is a real job
        # in this tree that owes no row, and this is the reason.
        on_push = VALID_WORKFLOW.replace('  pull_request:\n    branches: ["**"]\n', "")
        produced, found = checks_table.workflow_checks(one(on_push))
        self.assertEqual([], found)
        self.assertEqual({}, produced)

    def test_a_matrix_appends_its_value_to_a_fixed_name(self) -> None:
        matrixed = VALID_WORKFLOW.replace(
            "    runs-on: ubuntu-latest\n",
            "    runs-on: ${{ matrix.os }}\n"
            "    strategy:\n"
            "      matrix:\n"
            "        os: [ubuntu-latest, macos-latest]\n",
        )
        produced, found = checks_table.workflow_checks(one(matrixed))
        self.assertEqual([], found)
        self.assertEqual(
            ["an example check (macos-latest)", "an example check (ubuntu-latest)"],
            sorted(produced),
        )

    def test_a_matrix_named_in_the_job_name_is_substituted_instead(self) -> None:
        referenced = VALID_WORKFLOW.replace(
            "    name: an example check\n",
            "    name: an example check on ${{ matrix.os }}\n",
        ).replace(
            "    runs-on: ubuntu-latest\n",
            "    runs-on: ${{ matrix.os }}\n"
            "    strategy:\n"
            "      matrix:\n"
            "        os: [ubuntu-latest]\n",
        )
        produced, found = checks_table.workflow_checks(one(referenced))
        self.assertEqual([], found)
        self.assertEqual(["an example check on ubuntu-latest"], sorted(produced))

    def test_a_matrix_with_two_keys_is_refused_rather_than_guessed(self) -> None:
        two_keys = VALID_WORKFLOW.replace(
            "    runs-on: ubuntu-latest\n",
            "    runs-on: ubuntu-latest\n"
            "    strategy:\n"
            "      matrix:\n"
            "        os: [ubuntu-latest]\n"
            "        python: ['3.13']\n",
        )
        produced, found = checks_table.workflow_checks(one(two_keys))
        self.assertEqual({}, produced)
        self.assertEqual(["undecidable-workflow"], kinds(found))

    def test_a_matrix_carrying_include_is_refused(self) -> None:
        included = VALID_WORKFLOW.replace(
            "    runs-on: ubuntu-latest\n",
            "    runs-on: ubuntu-latest\n"
            "    strategy:\n"
            "      matrix:\n"
            "        os: [ubuntu-latest]\n"
            "        include:\n"
            "          - os: macos-latest\n",
        )
        produced, found = checks_table.workflow_checks(one(included))
        self.assertEqual({}, produced)
        self.assertEqual(["undecidable-workflow"], kinds(found))

    def test_a_name_that_is_an_expression_without_a_matrix_is_refused(self) -> None:
        expression = VALID_WORKFLOW.replace(
            "    name: an example check\n", "    name: ${{ github.event_name }}\n"
        )
        produced, found = checks_table.workflow_checks(one(expression))
        self.assertEqual({}, produced)
        self.assertEqual(["undecidable-workflow"], kinds(found))

    def test_a_file_that_is_not_yaml_is_refused(self) -> None:
        produced, found = checks_table.workflow_checks(one("name: [unclosed\n"))
        self.assertEqual({}, produced)
        self.assertEqual(["undecidable-workflow"], kinds(found))


EXCEPTED = [name for name, _ in checks_table.NOT_FROM_A_WORKFLOW]


class TheTwoDirections(unittest.TestCase):
    """The two arms of the done-condition, each with the nearest passing case.

    Every row set below carries the register's own names, derived from the
    register rather than written out, so an entry added to it does not red these
    tests for a reason none of them is about.
    """

    def test_a_matching_pair_refuses_nothing(self) -> None:
        self.assertEqual(
            [],
            checks_table.failures(
                ["an example check", *EXCEPTED],
                {"an example check": ".github/workflows/example.yml"},
            ),
        )

    def test_a_row_naming_a_check_that_does_not_run_is_refused(self) -> None:
        found = checks_table.failures(
            ["an example check", "a check that went away", *EXCEPTED],
            {"an example check": ".github/workflows/example.yml"},
        )
        self.assertEqual(["stale-row"], kinds(found))
        self.assertIn("a check that went away", found[0])

    def test_a_check_that_no_row_names_is_refused(self) -> None:
        found = checks_table.failures(
            ["an example check", *EXCEPTED],
            {
                "an example check": ".github/workflows/example.yml",
                "a check that arrived": ".github/workflows/new.yml",
            },
        )
        self.assertEqual(["unnamed-check"], kinds(found))
        self.assertIn("a check that arrived", found[0])


class TheRegisterOfChecksFromOutsideThisTree(unittest.TestCase):
    def test_every_entry_names_what_it_is(self) -> None:
        self.assertNotEqual((), checks_table.NOT_FROM_A_WORKFLOW)
        for name, reason in checks_table.NOT_FROM_A_WORKFLOW:
            self.assertNotEqual("", name.strip())
            self.assertNotEqual("", reason.strip())

    def test_an_entry_a_workflow_now_produces_is_refused(self) -> None:
        # The exemption exists because no workflow file carries that string. The
        # day one does, the exemption is the thing hiding a row nobody checked.
        produced = {
            name: ".github/workflows/example.yml"
            for name, _ in checks_table.NOT_FROM_A_WORKFLOW
        }
        rows = [name for name, _ in checks_table.NOT_FROM_A_WORKFLOW]
        found = checks_table.failures(rows, produced)
        self.assertEqual(["dangling-exception"], kinds(found))

    def test_an_entry_no_row_names_is_refused(self) -> None:
        found = checks_table.failures([], {})
        self.assertEqual(["unused-exception"], kinds(found))


class TheTreeItself(unittest.TestCase):
    """The real files, which is the near miss every fixture above is built from."""

    def setUp(self) -> None:
        self.workflows = checks_table.workflow_files(ROOT)
        document = os.path.join(ROOT, checks_table.TABLE_DOCUMENT)
        with open(document, encoding="utf-8") as handle:
            self.rows, self.table_refusals = checks_table.table_names(handle.read())

    def test_the_workflows_are_all_decidable(self) -> None:
        self.assertNotEqual([], self.workflows)
        _, found = checks_table.workflow_checks(self.workflows)
        self.assertEqual([], found)

    def test_the_table_is_read_and_holds(self) -> None:
        self.assertEqual([], self.table_refusals)
        produced, _ = checks_table.workflow_checks(self.workflows)
        self.assertEqual([], checks_table.failures(self.rows, produced))

    def test_the_command_exits_zero_on_the_tree(self) -> None:
        self.assertEqual(0, checks_table.main([ROOT]))

    def test_the_command_exits_one_on_a_root_with_no_document(self) -> None:
        # A wrong path must not read as a clean run. Without this the check
        # passes on any typo in the workflow.
        here = os.path.dirname(os.path.abspath(__file__))
        self.assertEqual(1, checks_table.main([here]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
