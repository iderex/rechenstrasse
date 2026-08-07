"""Deterministic pull request hygiene checks.

Issue #20. What this asserts is decidable from the pull request and the diff,
and nothing here is a judgement about quality. A hygiene check that needs an
opinion is a review in disguise, so where the issue asks for something no
reading of the pull request settles, this file says so and does not assert it.

The four arms, and what each one refuses:

  body-empty              a pull request body that is empty or only whitespace
  no-issue-reference      a body naming no issue
  head-is-default-branch  a head branch that is the repository's default branch
  generated-file-edited   a change to a generated file with no declaration
  commit-has-no-body      a commit message that is a subject line and nothing
                          else, trailers not counted as a body

Every failure line starts with the identifier of the arm that produced it. That
is not decoration. Two arms read the same input, and an empty body names no
issue as surely as it is empty, so a suite asserting only that something was
refused lets one arm stand in for another and a deleted arm stays green. The
identifier is what makes each arm provable on its own.

The issue asks for "the commit messages say what changed". Whether a message
says what changed is not decidable, so it is not asserted. What is decidable is
that a message has a body at all, and that the body is more than the trailers
git and the sign-off gate put there, which is the arm above. The rest is what
review is for, and this file does not pretend to cover it.

The generated set below is patterns rather than paths, because no generated file
is tracked in this repository yet. Every arm of that check is proven against
fixtures in test_hygiene.py and none of them has ever fired on a real file in
this tree. A pull request declares a legitimate regeneration with a line
"Regenerated: <path>" in its body, one per file, which is what separates a
regenerated file from a hand-edited one without asking anybody's opinion.

Input is the pull request as JSON, gathered by the workflow so that this file
reads no network and the fixtures in the suite are the same shape as the real
thing. Standard library only.
"""

import argparse
import fnmatch
import json
import re
import sys

# A file this repository generates rather than writes. Matched on the basename
# unless the pattern carries a slash, in which case it is matched on the whole
# path. Kept as a tuple so a reader can see the whole set at once.
GENERATED_PATTERNS = (
    "*.lock",
    "uv.lock",
    "poetry.lock",
    "requirements.lock",
    "packages.lock.json",
    "*.min.js",
    "*.min.css",
)

# A bare "#12", a keyword form "Closes #12", or the full issue URL. Lenient on
# purpose: the issue asks for a pull request that names no issue to be refused,
# not for a particular phrasing to be required.
ISSUE_REFERENCE = re.compile(r"(^|[^\w])#\d+\b")
ISSUE_URL = re.compile(r"github\.com/[^/\s]+/[^/\s]+/issues/\d+", re.IGNORECASE)

# A line of the form "Key: value" at the start of a line, which is what git and
# the sign-off gate append. A message whose whole body is trailers has no
# description in it.
TRAILER = re.compile(r"^[A-Za-z][A-Za-z-]*:\s")

REGENERATED = re.compile(r"^Regenerated:\s*(\S+)\s*$", re.MULTILINE)


def _matches(pattern, filename):
    """Glob match, on the basename unless the pattern names a directory."""
    if "/" in pattern:
        return fnmatch.fnmatch(filename, pattern)
    return fnmatch.fnmatch(filename.rsplit("/", 1)[-1], pattern)


def is_generated(filename):
    return any(_matches(p, filename) for p in GENERATED_PATTERNS)


def body_failures(pull_request):
    """The body is not empty and it names an issue."""
    body = pull_request.get("body") or ""
    if not body.strip():
        return [
            "body-empty: the pull request body is empty. Everything about a "
            "change goes in its body."
        ]
    if not (ISSUE_REFERENCE.search(body) or ISSUE_URL.search(body)):
        return [
            "no-issue-reference: the pull request body names no issue. Name the "
            "issue it closes, for example 'Closes #20'."
        ]
    return []


def head_failures(pull_request, repository):
    """The head branch is not the default branch."""
    head = pull_request.get("head_ref") or ""
    default = repository.get("default_branch") or ""
    if head and default and head == default:
        return [
            "head-is-default-branch: the head branch is '%s', which is the "
            "default branch. Open the change from a branch of its own." % head
        ]
    return []


def generated_failures(pull_request, files):
    """A generated file that changed is declared, or it is refused."""
    body = pull_request.get("body") or ""
    declared = set(REGENERATED.findall(body))
    undeclared = [
        f["filename"]
        for f in files
        if is_generated(f["filename"]) and f["filename"] not in declared
    ]
    if undeclared:
        return [
            "generated-file-edited: generated file(s) changed with no "
            "declaration: %s. "
            "A regenerated file carries a 'Regenerated: <path>' line in the body, "
            "one per file. A generated file is not edited by hand."
            % ", ".join(sorted(undeclared))
        ]
    return []


def has_message_body(message):
    """True when the message carries a description under its subject line.

    Trailers do not count. A message whose only body is the sign-off the DCO
    gate requires describes nothing, and that shape is the near miss this arm
    exists for.
    """
    lines = message.split("\n")
    if len(lines) < 2:
        return False
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if TRAILER.match(stripped):
            continue
        return True
    return False


def commit_failures(commits):
    """Every non-merge commit from a person carries a message body."""
    bare = []
    for commit in commits:
        if commit.get("author_is_bot"):
            continue
        message = commit.get("message") or ""
        if commit.get("parent_count", 1) > 1 or message.startswith("Merge "):
            continue
        if not has_message_body(message):
            subject = message.split("\n")[0]
            bare.append('%s ("%s")' % (commit.get("sha", "")[:7], subject))
    if bare:
        return [
            "commit-has-no-body: commit message(s) with no body: %s. A subject "
            "line alone cannot say what changed and what failure it prevents."
            % ", ".join(bare)
        ]
    return []


def check(pull_request, repository, files, commits):
    """Every arm, in a fixed order, returning the failures it found."""
    if pull_request.get("author_is_bot"):
        return []
    failures = []
    failures += body_failures(pull_request)
    failures += head_failures(pull_request, repository)
    failures += generated_failures(pull_request, files)
    failures += commit_failures(commits)
    return failures


def _read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _read_ndjson(path):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--pull-request", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--files", required=True)
    parser.add_argument("--commits", required=True)
    args = parser.parse_args(argv)

    failures = check(
        _read_json(args.pull_request),
        _read_json(args.repository),
        _read_ndjson(args.files),
        _read_ndjson(args.commits),
    )
    if not failures:
        print("Deterministic PR-hygiene checks passed.")
        return 0
    for failure in failures:
        print("::error::%s" % failure)
    return 1


if __name__ == "__main__":
    sys.exit(main())
