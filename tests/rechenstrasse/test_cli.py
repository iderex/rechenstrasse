"""What `python -m rechenstrasse` does today, held to what it says it does.

Issue #14 asks for the harness rather than for coverage, and these are the two
assertions the tree can currently carry: the version flag prints the version the
environment was built at, and a bare invocation is not mistaken for a run that
did something. The subcommands an operator will run are issue #59.
"""

import pytest

from rechenstrasse import __version__, cli


def test_the_version_flag_prints_the_installed_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as leaving:
        cli.main(["--version"])
    assert leaving.value.code == 0
    assert capsys.readouterr().out.strip() == __version__


def test_a_bare_invocation_exits_non_zero_rather_than_looking_like_a_run(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A bare call prints its usage and returns 2.

    Zero would be the failure. A pipeline that exits successfully having derived
    nothing is one whose exit status a caller cannot use, and a caller reading
    the status is the whole reason issue #59 gives the command three of them.
    """
    assert cli.main([]) == 2
    assert "usage: rechenstrasse" in capsys.readouterr().out
