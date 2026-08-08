"""The proof that the offline guard of `tests/conftest.py` bites.

Issue #14. The first arm is the one the issue asks for: a test that deliberately
opens a socket and is expected to fail. Two words on the marker carry it.
`strict=True` refuses the run where the body succeeded, which without that word
is reported as a curiosity on a green suite and is exactly the silent broken
guard this file exists against. `raises=` refuses the run where the body failed
for some other reason, so the arm is green only where the harness's own refusal
is what stopped it.

Deleting the `no_network` fixture from `tests/conftest.py` and running the suite
is how that is checked, and it is the check that was run before this landed:
four of the arms below turn red, this one among them.

The other three arms are separate entry points rather than restatements of the
first. A socket constructor, the convenience function that opens one for you,
and two name lookups are four different names in the `socket` module, and a
guard that patched one of them and lost the others would pass an arm-free suite.
"""

import socket

import pytest

from tests.conftest import NetworkAccessAttempted


@pytest.mark.xfail(
    raises=NetworkAccessAttempted,
    strict=True,
    reason=(
        "the harness refuses the network, so opening a socket has to fail here. "
        "A pass means the guard stopped working, and strict turns that into a "
        "red suite rather than a note nobody reads."
    ),
)
def test_a_test_that_opens_a_socket_does_not_get_one() -> None:
    socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def test_the_convenience_constructor_is_refused_as_well() -> None:
    with pytest.raises(NetworkAccessAttempted):
        socket.create_connection(("localhost", 9), timeout=1)


def test_a_name_lookup_is_refused_before_any_socket_exists() -> None:
    with pytest.raises(NetworkAccessAttempted):
        socket.getaddrinfo("localhost", 9)


def test_the_older_name_lookup_is_refused_too() -> None:
    with pytest.raises(NetworkAccessAttempted):
        socket.gethostbyname("localhost")


def test_the_refusal_is_not_the_error_a_disconnected_machine_gives() -> None:
    """The guard's exception is distinguishable from a real failed connection.

    On a runner with no route out, `OSError` is what a genuine attempt raises,
    and a proof that accepted `OSError` would pass there whether or not the
    guard existed. This asserts the type the guard raises is not that one.
    """
    assert not issubclass(NetworkAccessAttempted, OSError)
