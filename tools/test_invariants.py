"""Proof that each invariant bites, and that no rule ships without one.

Issue #19. Every rule below is tested against a file it refuses and against the
nearest file it must not refuse. The near miss is the point: an arm proven only
against something obviously wrong proves that the code runs, not that the rule
holds.

The fixtures are keyed by rule id and the suite walks `invariants.RULES` rather
than a list written here, so a rule added without a fixture fails this suite
rather than shipping as a comment with a workflow around it. That is the third
thing #19 asks for and it is the one that is easy to leave out.

A refusal is asserted by the rule that produced it and never by its truthiness.
Three of the four rules read the same files, so a fixture that trips two of them
would pass a test that only asks whether something was refused.

Standard library only, and no network.

    python tools/test_invariants.py
"""

import os
import sys
import unittest
from collections.abc import Iterable, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import invariants

# A workflow with nothing wrong with it. Every workflow fixture below is this
# one with exactly one thing changed, so a fixture's only defect is the one
# under test.
CLEAN_WORKFLOW = """name: Example

on:
  pull_request:
    branches: ["**"]

permissions: {}

jobs:
  example:
    name: example
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Checkout Repository
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - name: Do the thing
        run: echo done
"""

WORKFLOW = ".github/workflows/example.yml"

# One tripping file and one near miss per rule. The path matters as much as the
# text: a rule reads a file because of where it sits, so a fixture written at
# the wrong path proves nothing about the rule it is filed under.
FIXTURES: dict[str, dict[str, tuple[str, str]]] = {
    "no-float-above-the-boundary": {
        "trips": (
            "src/rechenstrasse/ppn/reading.py",
            '"""A stage above the boundary."""\n\nGAMMA_MINUS_ONE = 2.3e-5\n',
        ),
        "near_miss": (
            "src/rechenstrasse/ppn/reading.py",
            # One half written exactly, the way record 0006 asks for, plus the
            # decimal in a docstring where it is prose rather than a value.
            '"""A stage above the boundary. One half is 1/2 and never 0.5."""\n'
            "\nfrom fractions import Fraction\n\nHALF = Fraction(1, 2)\n"
            "ORDER = 2\n",
        ),
    },
    "no-networking-import": {
        "trips": (
            "src/rechenstrasse/document/reader.py",
            '"""A reader that fetches."""\n\nimport urllib.request\n',
        ),
        "near_miss": (
            "src/rechenstrasse/document/reader.py",
            # Reads a file and mentions a scheme in a string. Neither is an
            # import, and a rule that read the text rather than the imports
            # would refuse this one.
            '"""A reader that reads. It refuses an http:// source."""\n'
            "\nimport json\nimport os\n\nSCHEMES = ('http', 'https')\n"
            "__all__ = ['json', 'os', 'SCHEMES']\n",
        ),
    },
    "no-catch-all-except": {
        "trips": (
            "src/rechenstrasse/admissibility/gate.py",
            '"""A gate that shrugs."""\n\n\ndef run() -> None:\n'
            "    try:\n        decide()\n    except Exception:\n        pass\n",
        ),
        "near_miss": (
            "src/rechenstrasse/admissibility/gate.py",
            # The shape already in src/rechenstrasse/__init__.py: a named
            # exception, bound and re-raised as something the caller can read.
            '"""A gate that names what it catches."""\n\n\ndef run() -> None:\n'
            "    try:\n        decide()\n    except (ValueError, KeyError) as bad:\n"
            "        raise RuntimeError('refused') from bad\n",
        ),
    },
    "no-fixture-outside-the-repository": {
        "trips": (
            "tools/test_somewhere_else.py",
            '"""A test that reads somebody\'s machine."""\n\n'
            "CORPUS = '/var/lib/rechenstrasse/corpus'\n",
        ),
        "near_miss": (
            "tools/test_somewhere_else.py",
            # Relative to the file, which is the whole difference.
            '"""A test that reads this tree."""\n\nimport os\n\n'
            "CORPUS = os.path.join(os.path.dirname(__file__), '..', 'docs')\n",
        ),
    },
    "no-unpinned-action": {
        "trips": (
            WORKFLOW,
            CLEAN_WORKFLOW.replace(
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1",
                "actions/checkout@v7.0.1",
            ),
        ),
        # The near miss is the clean file itself: a commit with the release
        # written beside it. The one-character version of this mistake is
        # dropping the comment, which the suite tests separately.
        "near_miss": (WORKFLOW, CLEAN_WORKFLOW),
    },
    "no-write-permission-at-the-workflow-level": {
        "trips": (
            WORKFLOW,
            CLEAN_WORKFLOW.replace(
                "permissions: {}", "permissions:\n  contents: write"
            ),
        ),
        # The job below still asks for a write scope of its own in the near
        # miss, so this proves the rule reads the workflow level and not any
        # write scope anywhere in the file.
        "near_miss": (
            WORKFLOW,
            CLEAN_WORKFLOW.replace(
                "    permissions:\n      contents: read",
                "    permissions:\n      contents: write",
            ),
        ),
    },
    "checkout-does-not-persist-credentials": {
        "trips": (
            WORKFLOW,
            CLEAN_WORKFLOW.replace(
                "        with:\n          persist-credentials: false\n", ""
            ),
        ),
        # A different action carrying no `with:` block at all, which the rule
        # must not reach for.
        "near_miss": (
            WORKFLOW,
            CLEAN_WORKFLOW.replace(
                "      - name: Do the thing\n        run: echo done\n",
                "      - name: Do the thing\n"
                "        uses: astral-sh/setup-uv"
                "@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0\n",
            ),
        ),
    },
}


def arms(failures: Iterable[str]) -> list[str]:
    return sorted(failure.split(":", 1)[0] for failure in failures)


def assert_arm(case: unittest.TestCase, failures: Sequence[str], arm: str) -> None:
    case.assertIn(arm, arms(failures), f"expected {arm}, got {failures}")


class NoRuleShipsWithoutAFixture(unittest.TestCase):
    def test_every_rule_has_a_tripping_fixture_and_a_near_miss(self) -> None:
        # The rule this issue asks for by name. Walks the rules rather than the
        # fixtures, so adding a rule and forgetting its proof fails here.
        for rule in invariants.RULES:
            with self.subTest(rule=rule.id):
                self.assertIn(rule.id, FIXTURES)
                self.assertIn("trips", FIXTURES[rule.id])
                self.assertIn("near_miss", FIXTURES[rule.id])

    def test_every_rule_has_an_operator(self) -> None:
        for rule in invariants.RULES:
            with self.subTest(rule=rule.id):
                self.assertIn(rule.id, invariants.OPERATOR_IDS)

    def test_no_fixture_names_a_rule_that_does_not_exist(self) -> None:
        # The other direction. A fixture left behind by a deleted rule reads as
        # coverage and proves nothing.
        self.assertEqual(sorted(FIXTURES), sorted(rule.id for rule in invariants.RULES))

    def test_every_rule_says_what_it_prevents(self) -> None:
        for rule in invariants.RULES:
            with self.subTest(rule=rule.id):
                self.assertNotEqual("", rule.prevents.strip())
                self.assertNotEqual((), rule.subjects)


class EveryRuleBites(unittest.TestCase):
    def test_the_tripping_fixture_is_refused_by_its_own_rule_and_no_other(
        self,
    ) -> None:
        for rule in invariants.RULES:
            with self.subTest(rule=rule.id):
                failures = invariants.failures([FIXTURES[rule.id]["trips"]])
                assert_arm(self, failures, rule.id)
                self.assertEqual([rule.id], sorted(set(arms(failures))), failures)

    def test_the_near_miss_is_refused_by_nothing(self) -> None:
        for rule in invariants.RULES:
            with self.subTest(rule=rule.id):
                self.assertEqual(
                    [], invariants.failures([FIXTURES[rule.id]["near_miss"]])
                )


class WhereEachRuleReaches(unittest.TestCase):
    def test_the_float_rule_does_not_read_the_tooling(self) -> None:
        # Its subject is the pipeline above the boundary. A float in a tool is
        # not what record 0006 is about, and a rule that refused one would be
        # refused itself the first time somebody wrote a benchmark.
        path, text = FIXTURES["no-float-above-the-boundary"]["trips"]
        self.assertEqual([], invariants.failures([("tools/timing.py", text)]))
        self.assertNotEqual([], invariants.failures([(path, text)]))

    def test_the_fixture_rule_reads_test_files_only(self) -> None:
        path, text = FIXTURES["no-fixture-outside-the-repository"]["trips"]
        self.assertEqual([], invariants.failures([("tools/somewhere_else.py", text)]))
        self.assertNotEqual([], invariants.failures([(path, text)]))

    def test_a_file_outside_every_subject_is_not_read(self) -> None:
        _, text = FIXTURES["no-networking-import"]["trips"]
        self.assertEqual([], invariants.failures([("docs/example.py", text)]))

    def test_a_file_that_does_not_parse_is_refused_rather_than_skipped(self) -> None:
        failures = invariants.failures([("src/rechenstrasse/broken.py", "def (:\n")])
        assert_arm(self, failures, "unparsable")


class ExemptionsCannotOutliveTheirFiles(unittest.TestCase):
    def root(self) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def test_every_exempt_path_exists_in_the_tree(self) -> None:
        # A waiver naming a file nobody can find is a waiver nobody can retire.
        for rule in invariants.RULES:
            for path in rule.exempt:
                with self.subTest(rule=rule.id, path=path):
                    full = os.path.join(self.root(), path.replace("/", os.sep))
                    self.assertTrue(os.path.isfile(full), path)

    def test_nothing_is_exempt_today(self) -> None:
        # A negative disclosure, held to the tree rather than written in a
        # comment. When this fails, a rule has stopped reading something and the
        # diff that did it is the place to argue about whether it should.
        self.assertEqual([], [rule.id for rule in invariants.RULES if rule.exempt])


class TheWorkflowRulesInDetail(unittest.TestCase):
    def test_a_commit_with_no_version_comment_is_refused(self) -> None:
        # The one-character version of the pinning mistake: the right commit,
        # and nothing saying which release it is.
        text = CLEAN_WORKFLOW.replace(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1",
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        )
        failures = invariants.failures([(WORKFLOW, text)])
        assert_arm(self, failures, "no-unpinned-action")

    def test_a_local_action_is_not_a_pinning_question(self) -> None:
        text = CLEAN_WORKFLOW.replace(
            "        uses: actions/checkout"
            "@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1\n"
            "        with:\n          persist-credentials: false\n",
            "        uses: ./.github/actions/local\n",
        )
        self.assertEqual([], invariants.failures([(WORKFLOW, text)]))

    def test_a_missing_permissions_block_is_refused(self) -> None:
        # Absent is not the same as read-only. Without a block the default is a
        # repository setting, which is not a property of this file.
        text = CLEAN_WORKFLOW.replace("permissions: {}\n\n", "")
        failures = invariants.failures([(WORKFLOW, text)])
        assert_arm(self, failures, "no-write-permission-at-the-workflow-level")

    def test_write_all_at_the_workflow_level_is_refused(self) -> None:
        text = CLEAN_WORKFLOW.replace("permissions: {}", "permissions: write-all")
        failures = invariants.failures([(WORKFLOW, text)])
        assert_arm(self, failures, "no-write-permission-at-the-workflow-level")

    def test_read_all_at_the_workflow_level_is_not_refused(self) -> None:
        text = CLEAN_WORKFLOW.replace("permissions: {}", "permissions: read-all")
        self.assertEqual([], invariants.failures([(WORKFLOW, text)]))

    def test_persist_credentials_true_is_refused(self) -> None:
        # Written out rather than omitted, which is the shape somebody reaches
        # for when a later step needs to push.
        text = CLEAN_WORKFLOW.replace(
            "persist-credentials: false", "persist-credentials: true"
        )
        failures = invariants.failures([(WORKFLOW, text)])
        assert_arm(self, failures, "checkout-does-not-persist-credentials")

    def test_a_workflow_outside_the_workflows_directory_is_not_read(self) -> None:
        text = CLEAN_WORKFLOW.replace(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1",
            "actions/checkout@v7.0.1",
        )
        self.assertEqual([], invariants.failures([("docs/example.yml", text)]))

    def test_a_workflow_that_does_not_parse_is_refused_rather_than_skipped(
        self,
    ) -> None:
        failures = invariants.failures([(WORKFLOW, "name: [unclosed\n")])
        assert_arm(self, failures, "unparsable")


class TheTreeAsItStands(unittest.TestCase):
    def root(self) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def test_the_tree_is_refused_by_nothing(self) -> None:
        files = invariants.source_files(self.root())
        self.assertNotEqual([], files)
        self.assertEqual([], invariants.failures(files))

    def test_the_command_exits_zero_on_the_tree(self) -> None:
        self.assertEqual(0, invariants.main([self.root()]))

    def test_the_command_exits_one_on_a_root_with_no_source(self) -> None:
        # A wrong root must not read as a clean run. Without this the check
        # passes on any typo in the workflow.
        self.assertEqual(1, invariants.main([os.path.dirname(__file__)]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
