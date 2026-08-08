"""A test that fails, with nothing else wrong with it.

Issue #15. The `tests` check runs this file in a step that requires the run to
come out red, so a job that reports green whatever the suite said is caught here
rather than on the change it waved through.

One defect, and it is the assertion. The linter, the formatter and the type
checker are run against this file in the same step and all three accept it, so a
red `tests` on it means the suite and not somebody else's rule.

The default run never reads it: that run is given `tests/` and this file is not
in it. `tools/suites.py` carries the same statement as data, so a reader of a
green run is told this file exists and why it is not a suite.
"""


def test_one_is_not_two() -> None:
    counted = 1
    assert counted == 2, "the failing assertion this fixture exists to be"
