"""Proof that each arm of the hygiene check bites, and bites for its own reason.

Issue #20. Every arm below is tested twice: once with an input it refuses, and
once with the nearest input it must not refuse. The near miss is the point. An
arm proven only against something obviously wrong proves that the code runs, not
that the rule holds, so each neighbour here is the one-character mistake
somebody will actually make.

Standard library only, and no network: the fixtures are the same shape the
workflow gathers from the API, so a change to that shape breaks the suite rather
than the gate.

    python3 .github/pr-hygiene/test_hygiene.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hygiene  # noqa: E402


def pr(body="Closes #20", head_ref="a-branch", author_is_bot=False):
    return {"body": body, "head_ref": head_ref, "author_is_bot": author_is_bot}


def repo(default_branch="main"):
    return {"default_branch": default_branch}


def files(*names):
    return [{"filename": n} for n in names]


def commit(message, sha="abc1234", parents=1, bot=False):
    return {
        "sha": sha,
        "message": message,
        "parent_count": parents,
        "author_is_bot": bot,
    }


GOOD_COMMIT = commit("Add the thing\n\nWhat it prevents, in a sentence.")


class BodyIsNotEmpty(unittest.TestCase):
    def test_whitespace_only_body_is_refused(self):
        self.assertTrue(hygiene.body_failures(pr(body="  \n\t \n")))

    def test_none_body_is_refused(self):
        self.assertTrue(hygiene.body_failures(pr(body=None)))

    def test_one_character_more_than_whitespace_is_not_refused_for_emptiness(self):
        # The near miss: a body that is barely there is not an empty body. It
        # still has to name an issue, which is the next arm and not this one.
        failures = hygiene.body_failures(pr(body="x"))
        self.assertEqual(1, len(failures))
        self.assertIn("names no issue", failures[0])


class BodyNamesAnIssue(unittest.TestCase):
    def test_prose_naming_the_issue_without_a_hash_is_refused(self):
        # The near miss for this arm. "issue 20" reads to a person as a
        # reference and links to nothing.
        self.assertTrue(hygiene.body_failures(pr(body="Fixes issue 20 at last.")))

    def test_a_bare_hash_with_no_number_is_refused(self):
        self.assertTrue(hygiene.body_failures(pr(body="A heading # and no number")))

    def test_a_bare_number_reference_passes(self):
        self.assertEqual([], hygiene.body_failures(pr(body="Work on #20.")))

    def test_a_keyword_form_passes(self):
        self.assertEqual([], hygiene.body_failures(pr(body="Closes #20")))

    def test_a_full_issue_url_passes(self):
        self.assertEqual(
            [],
            hygiene.body_failures(
                pr(body="See https://github.com/iderex/rechenstrasse/issues/20")
            ),
        )

    def test_an_all_digit_colour_code_counts_as_a_reference(self):
        # Recorded rather than fixed. A body containing "#123456" satisfies this
        # arm without naming an issue, and tightening the pattern would refuse
        # legitimate references instead. The arm exists to catch a body that
        # names nothing, and this input is not that case.
        self.assertEqual([], hygiene.body_failures(pr(body="The colour #123456.")))


class HeadIsNotTheDefaultBranch(unittest.TestCase):
    def test_head_equal_to_the_default_branch_is_refused(self):
        self.assertTrue(hygiene.head_failures(pr(head_ref="main"), repo("main")))

    def test_a_branch_whose_name_starts_with_the_default_is_not_refused(self):
        # The near miss: a prefix is not the branch. An arm written with a
        # startswith would refuse this one.
        self.assertEqual([], hygiene.head_failures(pr(head_ref="main-thing"), repo("main")))

    def test_a_repository_with_another_default_refuses_that_one_instead(self):
        self.assertTrue(hygiene.head_failures(pr(head_ref="trunk"), repo("trunk")))
        self.assertEqual([], hygiene.head_failures(pr(head_ref="main"), repo("trunk")))


class GeneratedFilesAreNotEditedByHand(unittest.TestCase):
    def test_an_undeclared_lockfile_change_is_refused(self):
        self.assertTrue(
            hygiene.generated_failures(pr(body="Closes #20"), files("uv.lock"))
        )

    def test_a_declared_lockfile_change_passes(self):
        self.assertEqual(
            [],
            hygiene.generated_failures(
                pr(body="Closes #20\n\nRegenerated: uv.lock\n"), files("uv.lock")
            ),
        )

    def test_a_declaration_for_a_different_path_does_not_cover_this_one(self):
        # The near miss that matters most: a body that declares something, so a
        # check looking only for the word would pass it.
        self.assertTrue(
            hygiene.generated_failures(
                pr(body="Closes #20\n\nRegenerated: poetry.lock\n"), files("uv.lock")
            )
        )

    def test_a_file_that_merely_contains_the_word_lock_is_not_generated(self):
        self.assertEqual(
            [], hygiene.generated_failures(pr(), files("docs/lockfile-notes.md"))
        )
        self.assertEqual([], hygiene.generated_failures(pr(), files("mylock.json")))

    def test_a_generated_file_in_a_subdirectory_is_still_generated(self):
        self.assertTrue(hygiene.generated_failures(pr(), files("tools/uv.lock")))

    def test_the_pattern_set_matches_nothing_tracked_in_this_repository_today(self):
        # The disclosure in hygiene.py, held to by a test rather than by a
        # comment. When this fails, a generated file has entered the tree and
        # the arm above stops being fixture-only.
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        tracked = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for name in filenames:
                rel = os.path.relpath(os.path.join(dirpath, name), root)
                tracked.append(rel.replace(os.sep, "/"))
        self.assertEqual([], [t for t in tracked if hygiene.is_generated(t)])


class CommitMessagesCarryABody(unittest.TestCase):
    def test_a_subject_only_message_is_refused(self):
        self.assertTrue(hygiene.commit_failures([commit("Add the thing")]))

    def test_a_subject_and_a_blank_line_and_nothing_else_is_refused(self):
        self.assertTrue(hygiene.commit_failures([commit("Add the thing\n\n   \n")]))

    def test_a_message_whose_only_body_is_the_sign_off_is_refused(self):
        # The near miss this arm exists for. The sign-off gate puts this trailer
        # on every commit, so a message with nothing but a subject and a
        # sign-off passes anything that only counts non-blank lines.
        self.assertTrue(
            hygiene.commit_failures(
                [commit("Add the thing\n\nSigned-off-by: A Person <a@example.org>\n")]
            )
        )

    def test_one_line_of_description_above_the_trailers_passes(self):
        self.assertEqual(
            [],
            hygiene.commit_failures(
                [
                    commit(
                        "Add the thing\n\nWhat it prevents.\n\n"
                        "Signed-off-by: A Person <a@example.org>\n"
                    )
                ]
            ),
        )

    def test_a_merge_commit_is_exempt_by_its_parents(self):
        self.assertEqual([], hygiene.commit_failures([commit("Merge branch", parents=2)]))

    def test_a_merge_commit_is_exempt_by_its_subject(self):
        self.assertEqual(
            [], hygiene.commit_failures([commit("Merge pull request #1 from x")])
        )

    def test_a_bot_commit_is_exempt(self):
        self.assertEqual([], hygiene.commit_failures([commit("Bump a thing", bot=True)]))

    def test_the_arm_names_the_commit_it_refused(self):
        failures = hygiene.commit_failures([GOOD_COMMIT, commit("Bare", sha="deadbee0")])
        self.assertEqual(1, len(failures))
        self.assertIn("deadbee", failures[0])


class TheWholeCheck(unittest.TestCase):
    def test_a_clean_pull_request_produces_no_failures(self):
        self.assertEqual(
            [],
            hygiene.check(pr(), repo(), files("docs/decisions/0020-a.md"), [GOOD_COMMIT]),
        )

    def test_each_arm_reaches_the_whole_check(self):
        # Disabling one arm's input at a time, so a failure here says which arm
        # stopped biting rather than only that something did.
        cases = {
            "body": (pr(body=""), repo(), files(), [GOOD_COMMIT]),
            "issue": (pr(body="No reference here."), repo(), files(), [GOOD_COMMIT]),
            "branch": (pr(head_ref="main"), repo("main"), files(), [GOOD_COMMIT]),
            "generated": (pr(), repo(), files("uv.lock"), [GOOD_COMMIT]),
            "commit": (pr(), repo(), files(), [commit("Bare")]),
        }
        for name, arguments in cases.items():
            with self.subTest(arm=name):
                self.assertTrue(hygiene.check(*arguments), name)

    def test_a_bot_pull_request_is_exempt_from_every_arm(self):
        self.assertEqual(
            [],
            hygiene.check(
                pr(body="", head_ref="main", author_is_bot=True),
                repo("main"),
                files("uv.lock"),
                [commit("Bare")],
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
